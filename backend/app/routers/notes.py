from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Note, User
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services import note_service

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteOut])
def list_notes(
    q: str | None = Query(None, max_length=200, description="Search in title or content (case-insensitive)"),
    tag_id: int | None = Query(None, description="Only notes with this tag"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Note]:
    return note_service.list_notes(db, current_user, q, tag_id)


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    data: NoteCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Note:
    return note_service.create_note(db, current_user, data)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Note:
    return note_service.get_note(db, current_user, note_id)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Note:
    return note_service.update_note(db, current_user, note_id, data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    note_service.delete_note(db, current_user, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{note_id}/pin", response_model=NoteOut)
def toggle_pin(
    note_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Note:
    return note_service.toggle_pin(db, current_user, note_id)
