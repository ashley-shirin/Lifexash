from datetime import date

from pydantic import BaseModel

from app.schemas.task import TaskOut


class DashboardSummary(BaseModel):
    date: date
    tasks_total: int
    tasks_completed: int
    score: int | None  # 0–100, or null when the day has no tasks
    streak_days: int
    today_mood: int | None  # 1–5, or null when there's no journal entry for the day
    avg_mood_7d: float | None  # 1 decimal, over the entries of date-6 … date
    next_tasks: list[TaskOut]  # up to 3 incomplete tasks of the day, earliest first


class DayStat(BaseModel):
    date: date
    tasks_total: int
    tasks_completed: int
    score: int | None
    mood: int | None
