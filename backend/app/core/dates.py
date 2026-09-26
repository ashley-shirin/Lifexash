"""Date rules shared by several features."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta


def not_too_far_ahead(field_name: str) -> Callable[[date], date]:
    """Build a Pydantic validator that rejects a date more than 1 day after UTC today (→ 422).

    We compare with UTC "today": no time zone is more than 14 h ahead of UTC, so +1 day always
    covers the user's local today, wherever they are (and whatever zone the server runs in).
    """

    def validate(value: date) -> date:
        latest = datetime.now(UTC).date() + timedelta(days=1)
        if value > latest:
            raise ValueError(f"{field_name} cannot be in the future")
        return value

    return validate
