from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Task, User
from app.schemas.task import TaskCreate, TaskUpdate

MAX_RANGE_DAYS = 366


def _get_owned_task(db: Session, user: User, task_id: int) -> Task:
    # Filtering by user_id here means another user's task looks exactly like a missing one (404).
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


def list_tasks(db: Session, user: User, start: date, end: date) -> list[Task]:
    """Tasks from start to end (both inclusive), ordered by day then time."""
    if start > end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "start must be on or before end")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"Date range cannot be longer than {MAX_RANGE_DAYS} days"
        )

    query = (
        select(Task)
        .where(Task.user_id == user.id, Task.task_date.between(start, end))
        .order_by(Task.task_date, Task.task_time, Task.id)
    )
    return list(db.scalars(query))


def get_task(db: Session, user: User, task_id: int) -> Task:
    return _get_owned_task(db, user, task_id)


def create_task(db: Session, user: User, data: TaskCreate) -> Task:
    task = Task(user_id=user.id, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, user: User, task_id: int, data: TaskUpdate) -> Task:
    task = _get_owned_task(db, user, task_id)
    # exclude_unset: only fields the client actually sent, so missing fields stay unchanged.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, user: User, task_id: int) -> None:
    task = _get_owned_task(db, user, task_id)
    db.delete(task)
    db.commit()


def toggle_task(db: Session, user: User, task_id: int) -> Task:
    task = _get_owned_task(db, user, task_id)
    task.is_completed = not task.is_completed
    # func.now() = MySQL's NOW(), the same clock that fills created_at/updated_at.
    task.completed_at = func.now() if task.is_completed else None
    db.commit()
    db.refresh(task)
    return task
