"""Add 14 days of sample tasks and journal entries for ONE user (dev / screenshots only).

Run from backend/ (venv active):
    python -m scripts.seed_demo a@example.com            # dry run: only shows what it would add
    python -m scripts.seed_demo a@example.com --yes      # really adds the rows

Safety:
- Only inserts rows for the user with that email. It never updates or deletes anything.
- A day that already has tasks (or a journal entry) is skipped, so running it twice adds nothing new.

The pattern is fixed (not random), so the result is predictable on a fresh user:
today 3 of 5 done (60%), streak 7 days, 7-day average mood 3.8.
"""

import argparse
import sys
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import JournalEntry, Task, User
from app.models.task import TaskPriority

# One row per day, oldest first: (days before today, total tasks, completed tasks, mood or None)
PATTERN = [
    (13, 3, 3, 4),
    (12, 4, 2, 3),
    (11, 3, 1, 2),  # 33%: doesn't count
    (10, 2, 2, 4),
    (9, 0, 0, 3),  # no tasks at all
    (8, 4, 3, 4),
    (7, 5, 2, 2),  # 40%: breaks the streak, so the streak is the 7 days after it
    (6, 5, 4, 4),
    (5, 4, 2, 3),  # exactly 50%: counts
    (4, 3, 3, None),  # no journal entry
    (3, 4, 3, 5),
    (2, 2, 1, 3),  # exactly 50%: counts
    (1, 5, 5, 4),
    (0, 5, 3, 4),  # today: 3 of 5 done
]

TASKS = [  # (time, title, priority) — a day with N tasks uses the first N
    (time(8, 0), "Morning workout", TaskPriority.medium),
    (time(10, 0), "Deep work: portfolio project", TaskPriority.high),
    (time(13, 30), "Reply to emails", TaskPriority.low),
    (time(16, 0), "Study: SQL joins", TaskPriority.high),
    (time(19, 0), "Read 20 pages", TaskPriority.low),
]

JOURNAL = {
    1: "Rough day, low energy.",
    2: "Not great, but I got through it.",
    3: "An okay, ordinary day.",
    4: "Good day, got most things done.",
    5: "Great day! Everything clicked.",
}


def local_to_utc(day: date, at: time) -> datetime:
    """A wall-clock time on this computer → naive UTC, the way timestamps are stored in the DB."""
    # astimezone() on a naive datetime treats it as this computer's local time.
    return datetime.combine(day, at).astimezone(UTC).replace(tzinfo=None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed 14 days of demo data for one user.")
    parser.add_argument("email", help="email of an existing user")
    parser.add_argument("--yes", action="store_true", help="really write to the database")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="the last day to seed, YYYY-MM-DD (default: this computer's local date)",
    )
    args = parser.parse_args()
    first_day = args.today - timedelta(days=13)

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email))
        if user is None:
            print(f"No user with email {args.email!r}. Register that user first.")
            return 1

        # Two queries for the whole window, both filtered by this user's id only.
        days_with_tasks = set(
            db.scalars(
                select(Task.task_date)
                .where(Task.user_id == user.id, Task.task_date.between(first_day, args.today))
                .distinct()
            )
        )
        days_with_entry = set(
            db.scalars(
                select(JournalEntry.entry_date).where(
                    JournalEntry.user_id == user.id, JournalEntry.entry_date.between(first_day, args.today)
                )
            )
        )

        added_tasks = added_entries = 0
        skipped = []
        for days_back, total, completed, mood in PATTERN:
            day = args.today - timedelta(days=days_back)

            if day in days_with_tasks:
                skipped.append(f"{day} tasks")
            else:
                for i, (task_time, title, priority) in enumerate(TASKS[:total]):
                    done = i < completed  # the earliest tasks are the done ones
                    db.add(
                        Task(
                            user_id=user.id,
                            title=title,
                            task_date=day,
                            task_time=task_time,
                            priority=priority,
                            is_completed=done,
                            completed_at=local_to_utc(day, task_time) + timedelta(minutes=45) if done else None,
                        )
                    )
                    added_tasks += 1

            if mood is not None:
                if day in days_with_entry:
                    skipped.append(f"{day} journal")
                else:
                    db.add(JournalEntry(user_id=user.id, entry_date=day, mood=mood, content=JOURNAL[mood]))
                    added_entries += 1

        print(f"User: {user.name} <{user.email}> (id {user.id})")
        print(f"Days: {first_day} to {args.today}")
        print(f"Would add {added_tasks} tasks and {added_entries} journal entries.")
        if skipped:
            print("Skipped (already had data): " + ", ".join(skipped))

        if not args.yes:
            db.rollback()
            print("Dry run: nothing was written. Add --yes to really add the rows.")
            return 0

        db.commit()
        print("Done.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
