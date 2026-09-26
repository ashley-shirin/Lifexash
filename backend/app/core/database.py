from collections.abc import Generator

from sqlalchemy import Engine, MetaData, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Predictable constraint/index names, so Alembic migrations stay stable across machines.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Every table uses InnoDB (for foreign keys + transactions) and utf8mb4 (full Unicode, incl. emoji).
MYSQL_TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


def use_utc(engine: Engine) -> None:
    """Make every connection of this engine talk to MySQL in UTC.

    DATETIME columns have no time zone: MySQL fills CURRENT_TIMESTAMP / NOW() with the *session*
    time zone. Setting it to UTC on each new connection means all timestamps are stored in UTC,
    whatever zone the DB server runs in. (DATE columns like task_date are not affected.)
    """

    @event.listens_for(engine, "connect")
    def set_utc(dbapi_connection, _connection_record):
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
use_utc(engine)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: opens a DB session per request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
