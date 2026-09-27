import ssl
from collections.abc import Generator
from typing import Any

import certifi
from sqlalchemy import Engine, MetaData, create_engine, event, make_url
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


# A database on this machine gets no TLS settings; any other host gets required, verified TLS.
LOCAL_HOSTS = {None, "", "localhost", "127.0.0.1", "::1"}


def connect_args_for(url: str) -> dict[str, Any]:
    """Extra PyMySQL connect() arguments: verified TLS for every remote database, nothing for a local one.

    Local: PyMySQL's default ("preferred") mode encrypts if the server offers TLS, without checking the
    certificate, and falls back to plain if it doesn't. So a local MySQL works with or without TLS.
    Remote (e.g. TiDB Cloud, which refuses unencrypted connections): the server's certificate must be
    signed by a trusted CA from certifi's bundle (Mozilla's CA list, the same on every OS), and must
    be issued for the host name we connect to, or the connection is refused (no fallback to plain).
    So nobody in between can read or fake the traffic.
    TLS is on by default, so it can't be forgotten in production.
    """
    if make_url(url).host in LOCAL_HOSTS:
        return {}
    # create_default_context: verify_mode=CERT_REQUIRED and check_hostname=True.
    return {"ssl": ssl.create_default_context(cafile=certifi.where())}


def make_engine(url: str, **kwargs: Any) -> Engine:
    """Create an engine with TLS when needed and every session in UTC. Used by the app and by Alembic."""
    new_engine = create_engine(url, connect_args=connect_args_for(url), **kwargs)
    use_utc(new_engine)
    return new_engine


# pool_pre_ping: test a pooled connection before using it (the server may have closed it).
# pool_recycle: replace connections older than 5 minutes. TiDB Cloud Starter closes idle connections
# when it scales down, so we don't want to keep old ones around.
engine = make_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

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
