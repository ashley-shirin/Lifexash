from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Tag, User
from app.schemas.tag import TagCreate


def get_owned_tag(db: Session, user: User, tag_id: int) -> Tag:
    # Filtering by user_id means another user's tag looks exactly like a missing one (404).
    tag = db.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == user.id))
    if tag is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    return tag


def get_owned_tags(db: Session, user: User, tag_ids: list[int]) -> list[Tag]:
    """All the given tags in one query. 404 if any of them is missing or belongs to someone else."""
    if not tag_ids:
        return []
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user.id)))
    if len(tags) != len(set(tag_ids)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
    return tags


def list_tags(db: Session, user: User) -> list[Tag]:
    return list(db.scalars(select(Tag).where(Tag.user_id == user.id).order_by(func.lower(Tag.name))))


def create_tag(db: Session, user: User, data: TagCreate) -> Tag:
    duplicate = db.scalar(
        select(Tag.id).where(Tag.user_id == user.id, func.lower(Tag.name) == data.name.lower())
    )
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag already exists")

    tag = Tag(user_id=user.id, name=data.name)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        # Two requests at the same moment can both pass the check above; the unique key stops the second.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Tag already exists") from None
    db.refresh(tag)
    return tag


def delete_tag(db: Session, user: User, tag_id: int) -> None:
    tag = get_owned_tag(db, user, tag_id)
    # ON DELETE CASCADE on note_tags removes only the links; the notes themselves stay.
    db.delete(tag)
    db.commit()
