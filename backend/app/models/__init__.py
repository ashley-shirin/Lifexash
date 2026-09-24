# Import every model here so SQLAlchemy (and Alembic) know about all tables.
from app.models.journal_entry import JournalEntry
from app.models.note import Note
from app.models.note_tag import note_tags
from app.models.tag import Tag
from app.models.task import Task, TaskPriority
from app.models.user import User

__all__ = ["JournalEntry", "Note", "Tag", "Task", "TaskPriority", "User", "note_tags"]
