"""Timestamps leave the API as UTC with a "Z", so the browser can show "updated … ago" in any time zone.

No database needed: we build the schemas from plain objects, like SQLAlchemy rows (naive datetimes).
"""

from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

from app.schemas.note import NoteOut
from app.schemas.task import TaskOut

STORED = datetime(2026, 9, 26, 10, 16, 24)  # what MySQL hands back: naive, but UTC


def make_task(**overrides):
    fields = dict(
        id=1, title="Read", description=None, task_date=date(2026, 9, 26), task_time=time(9, 0),
        priority="medium", is_completed=False, completed_at=None, created_at=STORED, updated_at=STORED,
    )
    return SimpleNamespace(**(fields | overrides))


def test_naive_db_datetime_is_sent_as_utc_with_z():
    data = TaskOut.model_validate(make_task()).model_dump(mode="json")
    assert data["created_at"] == "2026-09-26T10:16:24Z"
    assert data["updated_at"] == "2026-09-26T10:16:24Z"


def test_open_task_has_null_completed_at():
    data = TaskOut.model_validate(make_task()).model_dump(mode="json")
    assert data["completed_at"] is None


def test_completed_at_is_utc_too():
    data = TaskOut.model_validate(make_task(is_completed=True, completed_at=STORED)).model_dump(mode="json")
    assert data["completed_at"] == "2026-09-26T10:16:24Z"


def test_aware_datetime_in_another_zone_is_converted_to_utc():
    india = timezone(timedelta(hours=5, minutes=30))
    note = SimpleNamespace(
        id=1, title="t", content="", is_pinned=False, tags=[],
        created_at=datetime(2026, 9, 26, 15, 46, 24, tzinfo=india), updated_at=STORED,
    )
    assert NoteOut.model_validate(note).model_dump(mode="json")["created_at"] == "2026-09-26T10:16:24Z"


def test_dates_are_not_touched():
    # task_date is the user's LOCAL day: it must stay a plain YYYY-MM-DD, no time zone.
    data = TaskOut.model_validate(make_task()).model_dump(mode="json")
    assert data["task_date"] == "2026-09-26"
    assert data["task_time"] == "09:00:00"
