from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.models import Note, Tag, User
from app.schemas.note import NoteCreate, NoteUpdate
from app.services.tag_service import get_owned_tag, get_owned_tags


def _get_owned_note(db: Session, user: User, note_id: int) -> Note:
    # Filtering by user_id means another user's note looks exactly like a missing one (404).
    note = db.scalar(
        select(Note).options(selectinload(Note.tags)).where(Note.id == note_id, Note.user_id == user.id)
    )
    if note is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    return note


def list_notes(db: Session, user: User, q: str | None, tag_id: int | None) -> list[Note]:
    """Pinned notes first, then the most recently updated. Optional text search and tag filter."""
    # selectinload: fetch the tags of ALL listed notes in one extra query (avoids N+1).
    query = select(Note).options(selectinload(Note.tags)).where(Note.user_id == user.id)

    q = (q or "").strip()
    if q:
        # autoescape=True escapes % and _ so they match literally instead of acting as wildcards.
        query = query.where(
            or_(Note.title.icontains(q, autoescape=True), Note.content.icontains(q, autoescape=True))
        )

    if tag_id is not None:
        get_owned_tag(db, user, tag_id)  # another user's tag → 404
        query = query.where(Note.tags.any(Tag.id == tag_id))

    query = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc(), Note.id.desc())
    return list(db.scalars(query))


def get_note(db: Session, user: User, note_id: int) -> Note:
    return _get_owned_note(db, user, note_id)


def create_note(db: Session, user: User, data: NoteCreate) -> Note:
    tags = get_owned_tags(db, user, data.tag_ids)
    note = Note(
        user_id=user.id, title=data.title, content=data.content, is_pinned=data.is_pinned, tags=tags
    )
    db.add(note)
    db.commit()
    return _get_owned_note(db, user, note.id)


def update_note(db: Session, user: User, note_id: int, data: NoteUpdate) -> Note:
    note = _get_owned_note(db, user, note_id)
    # exclude_unset: only fields the client actually sent, so missing fields stay unchanged.
    changes = data.model_dump(exclude_unset=True)

    if "tag_ids" in changes:
        note.tags = get_owned_tags(db, user, changes.pop("tag_ids"))
    for field, value in changes.items():
        setattr(note, field, value)

    # Tags live in note_tags, so a tags-only change wouldn't touch the notes row; bump updated_at by hand.
    if data.model_fields_set:
        note.updated_at = func.now()
    db.commit()
    return _get_owned_note(db, user, note.id)


def delete_note(db: Session, user: User, note_id: int) -> None:
    note = _get_owned_note(db, user, note_id)
    db.delete(note)
    db.commit()


def toggle_pin(db: Session, user: User, note_id: int) -> Note:
    note = _get_owned_note(db, user, note_id)
    note.is_pinned = not note.is_pinned
    # Pinning isn't an edit: write the old updated_at back explicitly, otherwise MySQL's
    # ON UPDATE CURRENT_TIMESTAMP would change it to "now".
    flag_modified(note, "updated_at")
    db.commit()
    return _get_owned_note(db, user, note.id)
