"""Unit tests for the pure streak/score functions. No database needed.

Run from backend/ (venv active):  python -m pytest -v
"""

from datetime import date, timedelta

from app.services.dashboard_service import compute_streak, day_score

TODAY = date(2026, 9, 26)
DONE = (2, 2)  # 100%: counts
HALF = (2, 1)  # 50%: counts
LOW = (4, 1)  # 25%: doesn't count


def days_ago(n: int, today: date = TODAY) -> date:
    return today - timedelta(days=n)


def test_empty_history_is_zero():
    assert compute_streak({}, TODAY) == 0


def test_today_counts():
    days = {TODAY: DONE, days_ago(1): DONE, days_ago(2): HALF}
    assert compute_streak(days, TODAY) == 3


def test_today_not_counting_yet_starts_from_yesterday():
    # Today is only 1 of 4 done, but the day isn't over: the streak from yesterday is kept.
    days = {TODAY: LOW, days_ago(1): DONE, days_ago(2): DONE}
    assert compute_streak(days, TODAY) == 2


def test_today_without_tasks_starts_from_yesterday():
    days = {days_ago(1): DONE}
    assert compute_streak(days, TODAY) == 1


def test_gap_breaks_the_streak():
    # days_ago(2) is missing entirely (no tasks), so the older days don't count.
    days = {TODAY: DONE, days_ago(1): DONE, days_ago(3): DONE, days_ago(4): DONE}
    assert compute_streak(days, TODAY) == 2


def test_zero_task_day_breaks_the_streak():
    # A day that is in the dict with 0 tasks has no score, so it breaks the streak too.
    days = {TODAY: DONE, days_ago(1): (0, 0), days_ago(2): DONE}
    assert compute_streak(days, TODAY) == 1


def test_low_day_in_the_middle_breaks_the_streak():
    days = {TODAY: DONE, days_ago(1): LOW, days_ago(2): DONE}
    assert compute_streak(days, TODAY) == 1


def test_exactly_50_percent_counts():
    days = {TODAY: (2, 1), days_ago(1): (4, 2), days_ago(2): (10, 5)}
    assert compute_streak(days, TODAY) == 3


def test_49_percent_does_not_count():
    assert compute_streak({TODAY: (100, 49)}, TODAY) == 0


def test_49_5_percent_does_not_count_even_though_it_rounds_to_50():
    assert day_score(200, 99) == 50
    assert compute_streak({TODAY: (200, 99)}, TODAY) == 0


def test_month_boundary():
    today = date(2026, 9, 1)
    days = {date(2026, 9, 1): DONE, date(2026, 8, 31): DONE, date(2026, 8, 30): HALF}
    assert compute_streak(days, today) == 3


def test_year_boundary():
    today = date(2027, 1, 1)
    days = {date(2027, 1, 1): DONE, date(2026, 12, 31): DONE}
    assert compute_streak(days, today) == 2


def test_lookback_is_capped_at_365_days():
    # Every day for 2 years counts, but we only look back 365 days: today + 365 earlier days.
    days = {days_ago(n): DONE for n in range(730)}
    assert compute_streak(days, TODAY) == 366


def test_future_days_are_ignored():
    days = {TODAY + timedelta(days=1): DONE}
    assert compute_streak(days, TODAY) == 0


def test_day_score():
    assert day_score(0, 0) is None
    assert day_score(5, 3) == 60
    assert day_score(3, 2) == 67
    assert day_score(8, 1) == 13  # 12.5 rounds up
    assert day_score(4, 4) == 100
