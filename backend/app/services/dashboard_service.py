"""Dashboard numbers. Nothing here is stored: everything is calculated from tasks and journal_entries.

The client always sends its own local "today"; this module never asks the server's clock.
"""

from datetime import date, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import JournalEntry, Task, User

STREAK_LOOKBACK_DAYS = 365
NEXT_TASKS_LIMIT = 3

# date → (total tasks, completed tasks)
DayCounts = dict[date, tuple[int, int]]


# ---- Pure functions: no database, no clock (unit-tested in tests/test_streak.py) ----


def day_score(total: int, completed: int) -> int | None:
    """Completion % rounded half-up (2 of 3 → 67). A day without tasks has no score: None, not 0."""
    if total == 0:
        return None
    # Integer maths for "round half up"; Python's round() would turn 12.5 into 12.
    return (200 * completed + total) // (2 * total)


def day_counts_for_streak(total: int, completed: int) -> bool:
    """A day counts if it has at least 1 task and at least 50% of them are done.

    Compared on whole numbers, not on the rounded score: 99 of 200 is 49.5%, which rounds to 50
    but must NOT count.
    """
    return total >= 1 and completed * 2 >= total


def compute_streak(days: DayCounts, today: date) -> int:
    """Number of consecutive counting days ending today.

    If today doesn't count yet we start from yesterday: the day isn't over, so it can't break the
    streak. We never look further back than STREAK_LOOKBACK_DAYS before today.
    """

    def counts(day: date) -> bool:
        return day_counts_for_streak(*days.get(day, (0, 0)))

    oldest = today - timedelta(days=STREAK_LOOKBACK_DAYS)
    day = today if counts(today) else today - timedelta(days=1)
    streak = 0
    while day >= oldest and counts(day):
        streak += 1
        day -= timedelta(days=1)
    return streak


# ---- Queries: one grouped query per data source, always filtered by the current user ----


def _task_counts(db: Session, user: User, start: date, end: date) -> DayCounts:
    """{day: (total, completed)} for days in start…end that have at least one task."""
    # Not func.sum(Task.is_completed): SQLAlchemy gives SUM() the type of its argument (Boolean),
    # so MySQL's 3 would come back as True → int(True) = 1. case() makes it a plain 1/0 integer.
    completed = func.sum(case((Task.is_completed, 1), else_=0))
    query = (
        select(Task.task_date, func.count(Task.id), completed)
        .where(Task.user_id == user.id, Task.task_date.between(start, end))
        .group_by(Task.task_date)
    )
    # MySQL returns SUM() as a Decimal, hence int().
    return {day: (int(total), int(completed)) for day, total, completed in db.execute(query)}


def _moods(db: Session, user: User, start: date, end: date) -> dict[date, int]:
    query = select(JournalEntry.entry_date, JournalEntry.mood).where(
        JournalEntry.user_id == user.id, JournalEntry.entry_date.between(start, end)
    )
    return {day: mood for day, mood in db.execute(query)}


def _next_tasks(db: Session, user: User, day: date) -> list[Task]:
    query = (
        select(Task)
        .where(Task.user_id == user.id, Task.task_date == day, Task.is_completed.is_(False))
        .order_by(Task.task_time, Task.id)
        .limit(NEXT_TASKS_LIMIT)
    )
    return list(db.scalars(query))


def get_summary(db: Session, user: User, today: date) -> dict:
    counts = _task_counts(db, user, today - timedelta(days=STREAK_LOOKBACK_DAYS), today)
    moods = _moods(db, user, today - timedelta(days=6), today)
    total, completed = counts.get(today, (0, 0))

    return {
        "date": today,
        "tasks_total": total,
        "tasks_completed": completed,
        "score": day_score(total, completed),
        "streak_days": compute_streak(counts, today),
        "today_mood": moods.get(today),
        "avg_mood_7d": round(sum(moods.values()) / len(moods), 1) if moods else None,
        "next_tasks": _next_tasks(db, user, today),
    }


def get_weekly(db: Session, user: User, end: date) -> list[dict]:
    """Exactly 7 items, oldest first (end-6 … end). Days without data are included with zeros/nulls."""
    start = end - timedelta(days=6)
    counts = _task_counts(db, user, start, end)
    moods = _moods(db, user, start, end)

    week = []
    for offset in range(7):
        day = start + timedelta(days=offset)
        total, completed = counts.get(day, (0, 0))
        week.append(
            {
                "date": day,
                "tasks_total": total,
                "tasks_completed": completed,
                "score": day_score(total, completed),
                "mood": moods.get(day),
            }
        )
    return week
