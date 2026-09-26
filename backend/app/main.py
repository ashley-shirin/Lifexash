from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, dashboard, health, journal, notes, tags, tasks

app = FastAPI(title="LifeXash API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
