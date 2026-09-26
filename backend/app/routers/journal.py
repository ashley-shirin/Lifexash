from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import JournalEntry, User
from app.schemas.journal import JournalCreate, JournalOut, JournalUpdate
from app.services import journal_service

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("", response_model=list[JournalOut])
def list_month(
    # pattern: FastAPI answers 422 by itself for anything that isn't YYYY-MM with a month 01–12.
    month: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Month, YYYY-MM"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JournalEntry]:
    year, month_number = map(int, month.split("-"))
    return journal_service.list_month(db, current_user, year, month_number)


@router.get("/date/{entry_date}", response_model=JournalOut)
def get_by_date(
    entry_date: date, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> JournalEntry:
    return journal_service.get_by_date(db, current_user, entry_date)


@router.post("", response_model=JournalOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    data: JournalCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> JournalEntry:
    return journal_service.create_entry(db, current_user, data)


@router.put("/{entry_id}", response_model=JournalOut)
def update_entry(
    entry_id: int,
    data: JournalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JournalEntry:
    return journal_service.update_entry(db, current_user, entry_id, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    journal_service.delete_entry(db, current_user, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
