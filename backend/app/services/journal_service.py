from calendar import monthrange
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JournalEntry, User
from app.schemas.journal import JournalCreate, JournalUpdate


def _get_owned_entry(db: Session, user: User, entry_id: int) -> JournalEntry:
    # Filtering by user_id means another user's entry looks exactly like a missing one (404).
    entry = db.scalar(select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_id == user.id))
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Journal entry not found")
    return entry


def list_month(db: Session, user: User, year: int, month: int) -> list[JournalEntry]:
    """All entries of one calendar month, oldest day first."""
    first = date(year, month, 1)
    last = date(year, month, monthrange(year, month)[1])  # monthrange → (weekday, number of days)
    query = (
        select(JournalEntry)
        .where(JournalEntry.user_id == user.id, JournalEntry.entry_date.between(first, last))
        .order_by(JournalEntry.entry_date)
    )
    return list(db.scalars(query))


def get_by_date(db: Session, user: User, entry_date: date) -> JournalEntry:
    entry = db.scalar(
        select(JournalEntry).where(JournalEntry.user_id == user.id, JournalEntry.entry_date == entry_date)
    )
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No journal entry for this date")
    return entry


def create_entry(db: Session, user: User, data: JournalCreate) -> JournalEntry:
    entry = JournalEntry(user_id=user.id, **data.model_dump())
    db.add(entry)
    try:
        db.commit()
    except IntegrityError:
        # No "does it exist?" check first: two requests at the same moment could both pass it.
        # The UNIQUE(user_id, entry_date) key is the only reliable guard, so we let it decide.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An entry for this date already exists") from None
    db.refresh(entry)
    return entry


def update_entry(db: Session, user: User, entry_id: int, data: JournalUpdate) -> JournalEntry:
    entry = _get_owned_entry(db, user, entry_id)
    # exclude_unset: only fields the client actually sent, so missing fields stay unchanged.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, user: User, entry_id: int) -> None:
    entry = _get_owned_entry(db, user, entry_id)
    db.delete(entry)
    db.commit()
