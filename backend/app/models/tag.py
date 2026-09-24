from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import MYSQL_TABLE_ARGS, Base
from app.models.note_tag import note_tags

if TYPE_CHECKING:
    from app.models.note import Note
    from app.models.user import User


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name"),
        MYSQL_TABLE_ARGS,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50))

    user: Mapped["User"] = relationship(back_populates="tags")
    notes: Mapped[list["Note"]] = relationship(
        secondary=note_tags, back_populates="tags", passive_deletes=True
    )
