# Pre-deploy — manual test checklist

Status: all rounds passed (2026-09-26).

Covers the `chore/pre-deploy` changes: UTC timestamps, config from the environment, the production build,
and a quick smoke test of all 5 features. Commands are PowerShell, run from `backend/` (venv active) or
`frontend/`.

## Setup

- [x] In `backend/.env`, rename `FRONTEND_URL` to `CORS_ORIGINS` and delete the `JWT_ALGORITHM` line (it's
      fixed to HS256 in code now). Compare with `backend/.env.example`.
- [x] `alembic upgrade head`, then `alembic current` → `81878a6609ca (head)`.
- [x] Restart the backend (`uvicorn app.main:app --reload`) and the frontend (`npm run dev`).

## Round 1 — Timestamps in UTC

- [x] `python -m pytest` → all pass (26), including `test_timestamps.py`.
- [x] Swagger, as User A: `POST /api/tasks` → `created_at` / `updated_at` end in **`Z`** and match the
      current **UTC** time (IST − 5:30). `task_date` is still the plain local day you sent (`YYYY-MM-DD`).
- [x] `PATCH /api/tasks/{id}/toggle` → `completed_at` ends in `Z`; toggle again → `null`.
- [x] `GET /api/notes`, `GET /api/auth/me`, a journal entry → every `*_at` ends in `Z`.
- [x] Existing data was converted: an old note's "updated … ago" in the browser matches when you really
      edited it (not 5½ hours off). The planner and journal still show every task and entry on the same day as before.
- [x] Browser: edit a note → the list shows **"updated just now"**.
- [x] DevTools → Sensors → Timezone ID `Pacific/Kiritimati` (UTC+14), reload `/notes` → still "updated just
      now" / the same "ago" text as before. (Before this change it was off by the zone difference.)

## Round 2 — Config errors (the app must refuse to start)

- [x] Short secret: `$env:JWT_SECRET="tooshort"; uvicorn app.main:app` → stops with
      `JWT_SECRET  String should have at least 32 characters`. The error does **not** print the value.
      Then `Remove-Item Env:JWT_SECRET`.
- [x] Missing both: `Rename-Item .env .env.bak`, start uvicorn → stops, listing `DATABASE_URL` and
      `JWT_SECRET` as missing. `Rename-Item .env.bak .env`.
- [x] Env beats `.env`: the short-secret test above failed even though `.env` has a valid secret.
- [x] CORS allowed: `curl.exe -i -H "Origin: http://localhost:5173" http://localhost:8000/api/health` →
      response has `access-control-allow-origin: http://localhost:5173`.
- [x] CORS blocked: the same with `-H "Origin: http://evil.example"` → **no** `access-control-allow-origin` header.
- [x] No secrets in git: `git grep -n -I "JWT_SECRET="` shows only `.env.example` (empty value).
      `git log --all --name-only --format= | Select-String "\.env"` shows only the two `.env.example` files.

## Round 3 — Production build

- [x] `npm run build` → exit 0, **no warnings**, files in `dist/`.
- [x] Bad URL: `$env:VITE_API_URL="localhost:8000/api"; npm run build` → fails with
      `VITE_API_URL is missing or not an http(s) URL`. Then `Remove-Item Env:VITE_API_URL`.
- [x] Missing: `Rename-Item .env .env.bak`, `npm run build` → the same error. `Rename-Item .env.bak .env`.
- [x] Preview the real build: add `http://localhost:4173` to `CORS_ORIGINS` in `backend/.env`
      (`http://localhost:5173,http://localhost:4173`), restart the backend, `npm run build; npm run preview` →
      <http://localhost:4173> logs in and loads data. (Without that origin → CORS error in the console.)

## Round 4 — Smoke test (browser, one pass per feature)

- [x] **Auth:** register a new user → dashboard. Log out → `/planner` redirects to login. Log in again.
- [x] **Tasks:** add a task for today, tick it, edit it, delete it. The progress bar updates.
- [x] **Notes:** create a note with a new inline tag, search for it, filter by the tag, pin it (it moves
      to the top), delete it.
- [x] **Journal:** add today's entry with a mood → the emoji appears on today in the calendar and the monthly
      average updates. Edit the mood, then delete the entry.
- [x] **Dashboard:** with 2 tasks today and 1 done → score 50%, the next task listed, today's mood shown, and
      the weekly chart has 7 days ending today.
- [x] **Isolation:** as User B, open User A's note URL → "Note not found".
