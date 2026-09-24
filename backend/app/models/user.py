from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import MYSQL_TABLE_ARGS, Base

if TYPE_CHECKING:
    from app.models.journal_entry import JournalEntry
    from app.models.note import Note
    from app.models.tag import Tag
    from app.models.task import Task


class User(Base):
    __tablename__ = "users"
    __table_args__ = MYSQL_TABLE_ARGS

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # passive_deletes=True: let MySQL's ON DELETE CASCADE remove child rows.
    tasks: Mapped[list["Task"]] = relationship(back_populates="user", passive_deletes=True)
    notes: Mapped[list["Note"]] = relationship(back_populates="user", passive_deletes=True)
    tags: Mapped[list["Tag"]] = relationship(back_populates="user", passive_deletes=True)
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="user", passive_deletes=True
    )
