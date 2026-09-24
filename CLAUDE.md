# LifeXash

## Current status
- Auth (register / login / me + frontend forms) is built but **NOT manually tested yet**.
- Next: create `backend/.env` with a `JWT_SECRET` → run `docs/auth-test-checklist.md` together → fix any bugs → then start the Tasks & Daily Planner feature.

Personal productivity PWA: daily planner (tasks), notes with tags, mood journal.
Stack: React (Vite) · FastAPI · MySQL 9.7 · SQLAlchemy 2.0 · Alembic · JWT auth.

## Folder structure

```
backend/app/
  core/       config, database session, security (JWT, bcrypt)
  models/     SQLAlchemy tables — one file per table, nothing else
  schemas/    Pydantic request/response models
  services/   business logic and all DB queries
  routers/    HTTP only: parse request, call a service, return response
  main.py     FastAPI app + router registration
backend/alembic/versions/   migration files
frontend/src/  api/ (axios client) · context/ (AuthContext) · components/ · pages/
```

Layering rule: routers only handle HTTP, services hold logic, models are tables — no queries in routers.

## Tables (6)

- `users` — email unique; store `password_hash` only, never the plain password.
- `tasks` — `task_date` and `task_time` are both required; priority low/medium/high.
- `notes` — belongs to a user; `is_pinned` flag.
- `tags` — name unique per user (`user_id`, `name`).
- `note_tags` — many-to-many join between notes and tags (composite PK, no extra columns).
- `journal_entries` — one entry per user per day (unique `user_id`, `entry_date`); `mood` is 1–5.
- All child tables use `ON DELETE CASCADE` from `users`.

## Rules

- Every query filters by the current user's id (`user_id == current_user.id`).
- Another user's record returns **404**, not 403 — never reveal that it exists.
- Never store score or streak — compute them from existing data when requested.
- Frontend always sends dates as `YYYY-MM-DD` for the user's **local** day
  (don't use `toISOString()`, it converts to UTC and can shift the date).

## Run

Backend (from `backend/`): `.\.venv\Scripts\Activate.ps1` then `uvicorn app.main:app --reload`
→ http://localhost:8000 (Swagger at /docs)
Frontend (from `frontend/`): `npm run dev`  → http://localhost:5173

Migrations (from `backend/`, venv active):
```powershell
alembic revision --autogenerate -m "describe change"   # review the file first!
alembic upgrade head
```

## Working with me

- I'm a fresher: when you use a new concept, explain it briefly (1–2 sentences).
- Ask before installing any package (pip or npm).
