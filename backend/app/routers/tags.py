from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Tag, User
from app.schemas.tag import TagCreate, TagOut
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_tags(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Tag]:
    return tag_service.list_tags(db, current_user)


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Tag:
    return tag_service.create_tag(db, current_user, data)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    tag_service.delete_tag(db, current_user, tag_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
