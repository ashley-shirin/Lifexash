from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority


def _clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Title cannot be blank")
    return value


def _clean_description(value: str | None) -> str | None:
    # An empty/whitespace-only description is stored as NULL, not "".
    if value is None:
        return None
    return value.strip() or None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    task_date: date
    task_time: time
    priority: TaskPriority = TaskPriority.medium

    _title = field_validator("title")(_clean_title)
    _description = field_validator("description")(_clean_description)


class TaskUpdate(BaseModel):
    """Partial update: only the fields you send are changed."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    task_date: date | None = None
    task_time: time | None = None
    priority: TaskPriority | None = None

    _description = field_validator("description")(_clean_description)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Title cannot be null")
        return _clean_title(value)

    # These columns are NOT NULL, so "leave it out" is fine but an explicit null is not.
    @field_validator("task_date", "task_time", "priority")
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    task_date: date
    task_time: time
    priority: TaskPriority
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
