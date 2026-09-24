from sqlalchemy import Column, ForeignKey, Table

from app.core.database import MYSQL_TABLE_ARGS, Base

# Pure join table (no extra columns), so a plain Table is used instead of a model class.
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, index=True),
    **MYSQL_TABLE_ARGS,
)
