"""Checks on the dashboard QUERY (not the pure streak maths). Still no database needed.

Why test_streak.py couldn't catch the "completed is always 1" bug: those tests hand compute_streak a
ready-made dict like {day: (5, 3)}. The bug happened one step earlier, while SQLAlchemy turned MySQL's
SUM() result into Python, so the dict itself was already wrong ((5, 1)) before the pure function ran.
"""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy.dialects import mysql

from app.services.dashboard_service import _task_counts


class CaptureDb:
    """Stands in for a Session: remembers the query instead of running it, returns no rows."""

    def execute(self, query):
        self.query = query
        return []


def test_completed_count_is_not_converted_to_a_boolean():
    db = CaptureDb()
    _task_counts(db, SimpleNamespace(id=1), date(2026, 9, 20), date(2026, 9, 26))
    completed_column = db.query.selected_columns[2]

    # Do exactly what SQLAlchemy does with a MySQL row: MySQL/PyMySQL send SUM(...) as Decimal('3'),
    # then the column's type may convert it (a Boolean type would turn 3 into True).
    convert = completed_column.type.result_processor(mysql.dialect(), None)
    value = convert(Decimal(3)) if convert else Decimal(3)

    assert int(value) == 3
