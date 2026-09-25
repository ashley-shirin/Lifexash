# Tasks & Daily Planner — manual test checklist

Status: all rounds passed (2026-09-25).

## Setup

No migration needed — the `tasks` table already exists from the initial migration.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload       # http://localhost:8000/docs
```

Second terminal: `cd frontend` → `npm run dev` (http://localhost:5173).

You need **two users**. Register them in Swagger if they don't exist yet:
- **User A**: `a@example.com` / `password123`
- **User B**: `b@example.com` / `password123`

In Swagger, log in as A, copy the `access_token`, click **Authorize** and paste it.

## Round 1 — Swagger: create + validation (as User A)

- [x] `POST /api/tasks` `{"title":"Gym","task_date":"2026-09-25","task_time":"18:00"}` → **201**; `priority` is `"medium"`, `is_completed` false, `completed_at` null. Note the `id` (call it **T1**).
- [x] Create `{"title":"Standup","task_date":"2026-09-25","task_time":"09:30","priority":"high","description":"Daily sync"}` → **201**.
- [x] Create `{"title":"Call mom","task_date":"2026-09-26","task_time":"08:00","priority":"low"}` → **201**.
- [x] Title `"   "` → **422** "Title cannot be blank".
- [x] Title with 201 characters → **422**.
- [x] `"priority":"urgent"` → **422**.
- [x] Leave out `task_time` → **422** (time is required).
- [x] `"task_date":"25-09-2026"` → **422**.
- [x] `"title":"  Padded  ","description":"   "` → **201**, title saved as `"Padded"`, description `null`.

## Round 2 — Swagger: listing

- [x] `GET /api/tasks?date=2026-09-25` → **200**, sorted by time: Standup (09:30) comes before Gym (18:00). "Call mom" (26th) is **not** in the list.
- [x] `GET /api/tasks?start=2026-09-25&end=2026-09-26` → all tasks from both days, the 25th first.
- [x] `GET /api/tasks` with no parameters → **422** "Send either ?date=… or both ?start= and ?end=".
- [x] `?date=2026-09-25&start=2026-09-25` (both modes) → **422**.
- [x] `?start=2026-09-26&end=2026-09-25` → **422** "start must be on or before end".
- [x] `?start=2026-01-01&end=2027-12-31` → **422** "cannot be longer than 366 days".
- [x] `?date=2030-01-01` (empty day) → **200** with `[]`.

## Round 3 — Swagger: get / update / toggle / delete

- [x] `GET /api/tasks/{T1}` → **200**.
- [x] `GET /api/tasks/999999` → **404** "Task not found".
- [x] `PUT /api/tasks/{T1}` `{"title":"Evening gym"}` → **200**; title changed, date/time/priority **unchanged**.
- [x] `PUT` `{"task_date":null}` → **422** (can't null a required field).
- [x] `PUT` `{"description":null}` → **200**, description cleared.
- [x] `PATCH /api/tasks/{T1}/toggle` → `is_completed: true`, `completed_at` has a timestamp.
- [x] Toggle again → `is_completed: false`, `completed_at: null`.
- [x] Click **Authorize → Logout**, then `GET /api/tasks?date=2026-09-25` → **401**. Authorize as A again.

## Round 4 — Swagger: User B can't see or touch A's tasks

Log in as **B**, Authorize with B's token.

- [x] `GET /api/tasks?date=2026-09-25` → **200** with `[]` (A's tasks are not listed).
- [x] `GET /api/tasks?start=2026-09-25&end=2026-09-26` → `[]`.
- [x] `GET /api/tasks/{T1}` → **404** "Task not found" (the same response as a task that doesn't exist, **not** 403).
- [x] `PUT /api/tasks/{T1}` `{"title":"hacked"}` → **404**.
- [x] `PATCH /api/tasks/{T1}/toggle` → **404**.
- [x] `DELETE /api/tasks/{T1}` → **404**.
- [x] Authorize as **A** again → `GET /api/tasks/{T1}` → still there, title **not** "hacked", not toggled.

## Round 5 — Browser: day view (log in as A)

- [x] Planner opens on **today**, with a "Today" tag next to the date heading and the Today button disabled.
- [x] ← Prev / Next → move one day. The URL changes to `/planner?date=…`.
- [x] Go to 25 Sep 2026: tasks are in time order and show a checkbox, title, time as "9:30 AM", and a coloured priority badge.
- [x] Refresh the page (F5) → you stay on the same day.
- [x] Date picker: pick any date → the list switches to that day.
- [x] Go to 31 Dec 2026, click Next → 1 Jan 2027 (month/year rollover works).
- [x] An empty day shows "No tasks for this day. Add one!" and no progress bar.
- [x] Visit `/planner?date=garbage` → falls back to today, no crash.

## Round 6 — Browser: add / edit / toggle / delete

- [x] On a day with tasks, tick one checkbox → the title gets crossed out and the progress bar updates, e.g. "1 of 2 done (50%)".
- [x] Tick all of them → "2 of 2 done (100%)". Refresh → the ticks are still there (saved on the server).
- [x] Go to a **future** day, click **+ Add task** → the date field is **that day** (not today), and the time is the **next full hour** (at 14:20 it shows 15:00).
- [x] Submit with an empty title → "Title is required." and no request is sent.
- [x] Add a task at 07:00 → the modal closes and the task appears **at the top** (time order).
- [x] Press **Esc** or **Cancel** in the modal → it closes and nothing is saved.
- [x] **Edit** a task → the modal shows its current values. Change the time to 23:00 → it moves to the bottom.
- [x] Edit a task and change its **date** to another day → it disappears from this day and appears on the new day.
- [x] **Delete** → a confirm box appears. **Cancel** → the task stays. **OK** → it's removed, and the progress bar updates.
- [x] Stop the backend (Ctrl+C) and tick a checkbox → a red "Can't reach the server" message appears, with no crash. Restart the backend.

## Round 7 — Browser: local date, not UTC

The app must use your **local** day. Between 00:00 and 05:30 IST, UTC is still on "yesterday",
so a `toISOString()` bug would show the wrong day. To test this without waiting until midnight:

- [x] Chrome DevTools (F12) → **⋮ → More tools → Sensors** → Location: **Other…** → Timezone ID `Pacific/Kiritimati` (UTC+14). Reload `/planner` (without `?date=`).
      The heading must show **Kiritimati's date** (usually one day ahead of India). That proves the app uses local time.
- [x] While still in that time zone, add a task → the Date field shows that same local day.
- [x] Reset Sensors → Location to **No override**.

## Round 8 — Browser: another user's tasks are invisible

- [x] Logged in as **A**, open `/planner?date=2026-09-25` → A's tasks are shown.
- [x] Log out (Profile page), log in as **B**, open `/planner?date=2026-09-25` → "No tasks for this day. Add one!"
- [x] As B, add a task on 25 Sep. Log back in as A → A does **not** see B's task, and A's own tasks are unchanged.
