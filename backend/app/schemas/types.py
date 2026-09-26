"""Field types shared by several response schemas."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def _as_utc(value: datetime) -> datetime:
    # MySQL DATETIME comes back "naive" (no time zone). We store UTC (see core/database.py),
    # so we just label it as UTC. Pydantic then outputs "2026-09-26T10:16:24Z".
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


# Use for created_at / updated_at / completed_at in *Out schemas. Not for DATE fields.
UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
