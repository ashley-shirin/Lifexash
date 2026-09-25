from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.tag import TagOut


def _clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Title cannot be blank")
    return value


def _unique_ids(ids: list[int]) -> list[int]:
    # [3, 3, 5] → [3, 5], keeping the order they were sent in.
    return list(dict.fromkeys(ids))


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    # Required, but may be "" (a title-only note). Not trimmed: whitespace/newlines can matter in a note.
    content: str
    tag_ids: list[int] = []
    is_pinned: bool = False

    _title = field_validator("title")(_clean_title)
    _tag_ids = field_validator("tag_ids")(_unique_ids)


class NoteUpdate(BaseModel):
    """Partial update: only the fields you send are changed. tag_ids replaces the whole tag list."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    tag_ids: list[int] | None = None
    is_pinned: bool | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Title cannot be null")
        return _clean_title(value)

    @field_validator("tag_ids")
    @classmethod
    def tag_ids_unique(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            raise ValueError("tag_ids cannot be null (send [] to remove all tags)")
        return _unique_ids(value)

    # "Leave it out" is fine, but an explicit null is not.
    @field_validator("content", "is_pinned")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    is_pinned: bool
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime

    @field_validator("tags")
    @classmethod
    def sort_tags(cls, value: list[TagOut]) -> list[TagOut]:
        return sorted(value, key=lambda tag: tag.name.lower())
