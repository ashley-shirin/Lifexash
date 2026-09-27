# LifeXash

## Current status
- Auth (register / login / me, JWT, protected routes) is **done and tested** — see `docs/auth-test-checklist.md`.
- Tasks & Daily Planner (CRUD, toggle, day view, progress bar) is **done and tested** — see `docs/tasks-test-checklist.md`.
- Notes + Tags (search, tag filter, pin, editor with inline tag create) is **done and tested** — see `docs/notes-test-checklist.md`.
- Journal (month calendar with mood emojis, monthly average, editor with mood picker, one entry per day)
  is **done and tested** — see `docs/journal-test-checklist.md`.
- Dashboard (greeting, today's score, streak, moods, next tasks, weekly chart, seed script) is
  **done and tested** — see `docs/dashboard-test-checklist.md`. Unit tests: `python -m pytest` from `backend/`.
- All 5 features are done and tested.
- Pre-deploy polish (UTC timestamps with "Z", config from env only, build check, README, DB backup +
  restore test) is **done and tested** — see `docs/pre-deploy-checklist.md`.
- Mobile layout + PWA (bottom nav, 44 px touch targets, manifest + icons, service worker, offline banner,
  update prompt) is **done and tested** (Rounds 1–6) — see `docs/mobile-pwa-test-checklist.md`.
- TiDB Cloud Starter support (verified TLS for remote DBs, pool_recycle, local-only backup scripts) is
  **done and tested** on the real cluster (AWS Singapore, database `lifexash`, migrated to head):
  `verify_remote_db.py` and Rounds 1, 4, 5, 6 of `docs/tidb-test-checklist.md` passed 2026-09-27.
  CHECK enforced on TiDB Starter (with tidb_enable_check_constraint = ON before migrating).
- **Deployed** (2026-09-27) with Render (`render.yaml`, `docs/deploy-guide.md`):
  site https://lifexash-web.onrender.com, API https://lifexash-api.onrender.com (free plan, Singapore;
  cold start about 1 min). Deploy guide step 4 passed. Mobile/PWA Round 7 passed on Android 2026-09-28
  (install, standalone, layout, offline banner, update prompt, no API data in Cache Storage).
  iPhone not tested. "Waking up the server" notice (`WakingUpNotice.jsx`, `api/slowRequests.js`)
  is unit-tested and was seen live on the phone after 20 minutes idle (2026-09-28).
- **Project complete.** Optional next ideas: iPhone test; a "Try again" button for failed requests;
  a read-only demo account.
- Deploying = push to `main` (Render auto-deploys; migrations run at start). Migrations must be backwards
  compatible (the old version serves until the new one is healthy).

Personal productivity PWA: daily planner (tasks), notes with tags, mood journal.
Stack: React (Vite) · FastAPI · MySQL 9.7 (local) / TiDB Cloud Starter (production) · SQLAlchemy 2.0 ·
Alembic · JWT auth.

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
- The service worker caches **only the app shell** (built HTML, JS, CSS, icons). **Never cache API
  responses** — no `runtimeCaching` in `vite.config.js`. They're private user data (a shared device) and go stale.
- Create DB engines only with `make_engine()` (`core/database.py`): it adds required, verified TLS
  (certifi CA bundle) for any host other than localhost / 127.0.0.1 / ::1, and UTC sessions. Never
  disable certificate checks or put SSL options in `DATABASE_URL`.
- TiDB differences: CHECK constraints are dropped unless `tidb_enable_check_constraint` is ON before
  migrating (it is on our cluster, and CHECK is enforced there; keep validating in Pydantic anyway); ids are unique but not consecutive (never depend on id order or gaps);
  ENUM values can only be appended.
- `scripts/backup_db.py` and `scripts/restore_test.py` are for local MySQL only (they refuse remote hosts).
- Before any command meant for TiDB, check the target in the same terminal:
  `python -c "from app.core.database import engine; print(engine.url)"`. Without `$env:DATABASE_URL`,
  everything silently uses local MySQL from `backend/.env`. Never report a remote result without that check.
- Mobile styles live in the `@media (max-width: 640px)` block at the end of `index.css`; touch targets ≥ 44 px.

## Run

Backend (from `backend/`): `.\.venv\Scripts\Activate.ps1` then `uvicorn app.main:app --reload`
→ http://localhost:8000 (Swagger at /docs)
Frontend (from `frontend/`): `npm run dev`  → http://localhost:5173
Frontend unit tests: `npm test` (Node's built-in `node --test`, no extra package; files `*.test.js`).

Service worker / PWA testing: it is **off in `npm run dev`**. Use `npm run build` then `npm run preview`
→ http://localhost:4173, and add `http://localhost:4173` to `CORS_ORIGINS` in `backend/.env` (comma-separated).
Icons: `node scripts/make-icons.mjs` regenerates `frontend/public/` icons.

Migrations (from `backend/`, venv active):
```powershell
alembic revision --autogenerate -m "describe change"   # review the file first!
alembic upgrade head
```

## Working with me

- I'm a fresher: when you use a new concept, explain it briefly (1–2 sentences).
- Ask before installing any package (pip or npm).
