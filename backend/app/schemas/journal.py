from datetime import UTC, date, datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_title(value: str | None) -> str | None:
    # An empty/whitespace-only title is stored as NULL, not "".
    if value is None:
        return None
    return value.strip() or None


def _content_not_blank(value: str) -> str:
    # Not trimmed (like notes): the text is stored exactly as written, it just can't be empty.
    if not value.strip():
        raise ValueError("Content cannot be blank")
    return value


def _not_too_far_ahead(value: date) -> date:
    # Compare with UTC "today": no time zone is more than 14 h ahead of UTC, so +1 day always
    # covers the user's local today, wherever they are (and whatever zone the server runs in).
    latest = datetime.now(UTC).date() + timedelta(days=1)
    if value > latest:
        raise ValueError("entry_date cannot be in the future")
    return value


class JournalCreate(BaseModel):
    entry_date: date
    # strict=True: only a real JSON integer is accepted ("3", true or 3.0 are rejected).
    mood: int = Field(ge=1, le=5, strict=True)
    title: str | None = Field(default=None, max_length=200)
    content: str

    _entry_date = field_validator("entry_date")(_not_too_far_ahead)
    _title = field_validator("title")(_clean_title)
    _content = field_validator("content")(_content_not_blank)


class JournalUpdate(BaseModel):
    """Partial update: only the fields you send are changed. The date of an entry can't be changed."""

    # extra="forbid": unknown fields (like entry_date) give a 422 instead of being silently ignored.
    model_config = ConfigDict(extra="forbid")

    mood: int | None = Field(default=None, ge=1, le=5, strict=True)
    title: str | None = Field(default=None, max_length=200)  # null (or "") clears the title
    content: str | None = None

    _title = field_validator("title")(_clean_title)

    # These columns are NOT NULL, so "leave it out" is fine but an explicit null is not.
    @field_validator("mood")
    @classmethod
    def mood_not_null(cls, value: int | None) -> int | None:
        if value is None:
            raise ValueError("Mood cannot be null")
        return value

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Content cannot be null")
        return _content_not_blank(value)


class JournalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_date: date
    mood: int
    title: str | None
    content: str
    created_at: datetime
    updated_at: datetime
