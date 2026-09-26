from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import AfterValidator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dates import not_too_far_ahead
from app.core.security import get_current_user
from app.models import User
from app.schemas.dashboard import DashboardSummary, DayStat
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    # AfterValidator runs our check after FastAPI has parsed the date, so a bad value → 422.
    date_: Annotated[
        date,
        Query(alias="date", description="The user's local today, YYYY-MM-DD"),
        AfterValidator(not_too_far_ahead("date")),
    ],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return dashboard_service.get_summary(db, current_user, date_)


@router.get("/weekly", response_model=list[DayStat])
def get_weekly(
    end: Annotated[
        date,
        Query(description="Last day of the 7-day window, YYYY-MM-DD"),
        AfterValidator(not_too_far_ahead("end")),
    ],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return dashboard_service.get_weekly(db, current_user, end)
