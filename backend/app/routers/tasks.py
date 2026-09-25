from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Task, User
from app.schemas.task import TaskCreate, TaskOut, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    date_: date | None = Query(None, alias="date", description="One day, YYYY-MM-DD"),
    start: date | None = Query(None, description="Range start (inclusive), use with end"),
    end: date | None = Query(None, description="Range end (inclusive), use with start"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    if date_ is not None and start is None and end is None:
        return task_service.list_tasks(db, current_user, date_, date_)
    if date_ is None and start is not None and end is not None:
        return task_service.list_tasks(db, current_user, start, end)
    raise HTTPException(
        status.HTTP_422_UNPROCESSABLE_ENTITY, "Send either ?date=YYYY-MM-DD or both ?start= and ?end="
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Task:
    return task_service.create_task(db, current_user, data)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Task:
    return task_service.get_task(db, current_user, task_id)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    return task_service.update_task(db, current_user, task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    task_service.delete_task(db, current_user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{task_id}/toggle", response_model=TaskOut)
def toggle_task(
    task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Task:
    return task_service.toggle_task(db, current_user, task_id)
