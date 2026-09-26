# Dashboard — manual test checklist

Status: all rounds passed (2026-09-26).

## Bug found during testing

- **What was wrong:** in Round 3, `summary` for the seeded Demo user said 1 of 5 done (score 20, streak 0)
  instead of 3 of 5 (score 60, streak 7). Every day with at least one done task showed exactly 1 done.
  The rows in the database were correct.
- **Root cause:** the query used `func.sum(Task.is_completed)`. SQLAlchemy gives `SUM()` the type of its
  argument (Boolean), so MySQL's `3` was converted to `True`, and `int(True)` is `1`. It was not
  `completed_at`: the dashboard never reads it, and the seed script already sets it for done tasks.
- **Fix:** sum `case((Task.is_completed, 1), else_=0)`, a plain integer. Regression test:
  `tests/test_dashboard_queries.py::test_completed_count_is_not_converted_to_a_boolean` (fails on the
  old query, passes now). The pure streak tests couldn't catch it: they receive the per-day counts ready-made.

The dates below are for testing on **Saturday 26 September 2026** (India, UTC+5:30). If you test on another
day, shift every date by the same number of days (or pass `--today 2026-09-26` to the seed script and
keep the dates as they are for the Demo user).

## Setup

No migration needed: the dashboard stores nothing, it only reads `tasks` and `journal_entries`.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt   # once: installs pytest
uvicorn app.main:app --reload         # http://localhost:8000/docs
```

Second terminal: `cd frontend` → `npm run dev` (http://localhost:5173).

Users:
- **User A**: `a@example.com` / `password123` (has data from the earlier checklists)
- **User B**: `b@example.com` / `password123` (has data from the earlier checklists)
- **Demo**: `demo@example.com` / `password123`: a brand-new user, created in Round 2 and seeded in Round 3

The expected values for A and B assume their data is what the earlier checklists left behind:
- A: tasks on 25 Sep (4 tasks, 1 done) and 26 Sep (1 task, done); journal on 23 Sep (mood 2), 25 Sep (5), 26 Sep (4), plus older ones.
- B: 25 Sep (1 task, not done); journal on 26 Sep (mood 3).

If yours differ, the rules still apply; only the numbers change.

Rules being tested:
- Day score = completed ÷ total, rounded half up. A day with 0 tasks has score `null`, not 0.
- A day counts toward the streak if it has ≥ 1 task and ≥ 50% done.
- Streak = consecutive counting days ending today; if today doesn't count *yet*, start from yesterday.

## Round 1 — pytest (streak function)

From `backend/` with the venv active:

```powershell
python -m pytest -v
```

- [x] **16 passed**. The tests cover: empty history · today counts · today not yet (starts from yesterday) · a gap
      breaks it · a 0-task day breaks it · a low day breaks it · exactly 50% counts · 49% doesn't · 49.5%
      doesn't (even though it rounds to 50) · month boundary 31 Aug → 1 Sep · year boundary · 365-day cap ·
      future days ignored · `day_score` rounding · `test_completed_count_is_not_converted_to_a_boolean`
      (in `test_dashboard_queries.py`: the done-count from MySQL stays 3, not `True` → 1).
- [x] Break it on purpose: in `dashboard_service.py` change `completed * 2 >= total` to `>`. Run again:
      `test_exactly_50_percent_counts` (and the other tests that use a 50% day) **fail**. Change it back and all 16 pass again.

## Round 2 — Swagger

In Swagger, log in (`POST /api/auth/login`), copy the `access_token`, click **Authorize** and paste it.
The two endpoints are under **dashboard**. You type the date into the `date` / `end` box.

### 2a — User A

- [x] `GET /api/dashboard/summary` · `date` = `2026-09-26` → **200**
      ```json
      {"date":"2026-09-26","tasks_total":1,"tasks_completed":1,"score":100,"streak_days":1,
       "today_mood":4,"avg_mood_7d":3.7,"next_tasks":[]}
      ```
      Streak 1: today (100%) counts, and 25 Sep (1 of 4 = 25%) doesn't. The 7-day average is (2+5+4)/3 = 3.67 → 3.7.
- [x] `GET /api/dashboard/weekly` · `end` = `2026-09-26` → **200**, **exactly 7 items**, 20 Sep … 26 Sep in order.
      20–24 Sep have `tasks_total` 0 and `score` **null** (not 0). 23 Sep has `mood` 2.
      25 Sep: `4, 1, score 25, mood 5`. 26 Sep: `1, 1, score 100, mood 4`.
- [x] Yesterday as "today": `summary` · `date` = `2026-09-25` → `score` 25, **`streak_days` 0**
      (25% doesn't count, so we start from 24 Sep, which has no tasks), `today_mood` 5, `avg_mood_7d` 3.5,
      `next_tasks` = the **3 incomplete** tasks of 25 Sep, earliest time first.
- [x] **Today doesn't count yet.** `POST /api/tasks` twice (note both ids):
      ```json
      {"title":"Streak test 1","task_date":"2026-09-26","task_time":"20:00"}
      ```
      ```json
      {"title":"Streak test 2","task_date":"2026-09-26","task_time":"21:00"}
      ```
      `summary` for `2026-09-26` → `tasks_total` 3, `tasks_completed` 1, `score` **33**, **`streak_days` 0**
      (today doesn't count yet, and yesterday doesn't count either). `next_tasks` = the two new tasks, 20:00 first.
- [x] **Exactly 50%.** `PATCH /api/tasks/{id}/toggle` on "Streak test 1" → `summary` → 2 of 3 = **67**, streak **1**.
      Now `DELETE` "Streak test 2" → 2 of 2 = 100, streak 1. Toggle "Streak test 1" again (1 of 2 = **50%**) →
      streak still **1** (50% counts). Then `DELETE` "Streak test 1" to clean up.

### 2b — User B (isolation)

Log in as B and Authorize with B's token.

- [x] `summary` · `date` = `2026-09-26` → `tasks_total` **0**, `tasks_completed` 0, `score` **null**,
      `streak_days` 0, `today_mood` 3, `avg_mood_7d` 3.0, `next_tasks` `[]`.
      None of A's tasks or moods show up.
- [x] `weekly` · `end` = `2026-09-26` → 25 Sep is `1, 0, score **0**` (tasks, none done: 0%, not null);
      26 Sep has `mood` 3; every other day is `0, 0, null, null`.

### 2c — Brand-new user (Demo) — empty data

- [x] `POST /api/auth/register`:
      ```json
      {"name":"Demo","email":"demo@example.com","password":"password123"}
      ```
      Log in as Demo and Authorize.
- [x] `summary` · `2026-09-26` → all zeros / nulls: `score` null, `streak_days` 0, `today_mood` null,
      `avg_mood_7d` null, `next_tasks` [].
- [x] `weekly` · `2026-09-26` → 7 items, all `0, 0, null, null`.

### 2d — Validation (any user)

- [x] `summary` · `date` = `2026-09-28` → **422** "Value error, date cannot be in the future".
- [x] `weekly` · `end` = `2026-09-28` → **422** "Value error, end cannot be in the future".
- [x] `summary` · `date` = `2026-09-27` (tomorrow) → **time-dependent** (limit = UTC today + 1 day):
      **after 05:30 IST** → **200**; **before 05:30 IST** → **422**.
- [x] `summary` · `date` = `2026-9-1` → **422** (must be `YYYY-MM-DD`). `2026-02-30` → **422** (not a real date).
- [x] `summary` with the `date` box empty → **422** "Field required".
- [x] Click **Authorize → Logout**, then `summary` · `2026-09-26` → **401** "Not authenticated".
- [x] A date long ago is fine: `summary` · `2025-01-01` → **200** with zeros/nulls.
- [x] Journal still works the same after the refactor: `POST /api/journal` with
      `{"entry_date":"2026-09-28","mood":3,"content":"x"}` → **422** "Value error, entry_date cannot be in the future".

## Round 3 — Seed script (Demo user)

From `backend/`, venv active.

- [x] **Without `--yes`** → dry run, nothing written:
      ```powershell
      python -m scripts.seed_demo demo@example.com --today 2026-09-26
      ```
      Prints `Would add 49 tasks and 13 journal entries.` and `Dry run: nothing was written.`
      Swagger `summary` for Demo is still all zeros.
- [x] Unknown email → `No user with email 'nobody@example.com'. Register that user first.`
      ```powershell
      python -m scripts.seed_demo nobody@example.com --yes
      ```
- [x] **Really seed**:
      ```powershell
      python -m scripts.seed_demo demo@example.com --today 2026-09-26 --yes
      ```
      → `Done.`
- [x] **Run it again** → `Would add 0 tasks and 0 journal entries.`, and the skipped list names every day. Nothing is duplicated.
- [x] **Other users untouched**: re-run the A (2a, first two) and B (2b) requests → exactly the same answers as before.

What the seed creates (days before 26 Sep → tasks done / total, mood):

| Date | Tasks | Score | Mood | Counts? |
|---|---|---|---|---|
| 13 Sep | 3/3 | 100 | 4 | ✔ |
| 14 Sep | 2/4 | 50 | 3 | ✔ |
| 15 Sep | 1/3 | 33 | 2 | ✘ |
| 16 Sep | 2/2 | 100 | 4 | ✔ |
| 17 Sep | — | null | 3 | ✘ (no tasks) |
| 18 Sep | 3/4 | 75 | 4 | ✔ |
| 19 Sep | 2/5 | 40 | 2 | ✘ |
| 20 Sep | 4/5 | 80 | 4 | ✔ |
| 21 Sep | 2/4 | 50 | 3 | ✔ |
| 22 Sep | 3/3 | 100 | — | ✔ |
| 23 Sep | 3/4 | 75 | 5 | ✔ |
| 24 Sep | 1/2 | 50 | 3 | ✔ |
| 25 Sep | 5/5 | 100 | 4 | ✔ |
| 26 Sep | 3/5 | 60 | 4 | ✔ |

Swagger as Demo:

- [x] `summary` · `2026-09-26` → `3` of `5`, `score` 60, **`streak_days` 7** (20–26 Sep; 19 Sep at 40% stops it),
      `today_mood` 4, `avg_mood_7d` **3.8** (23 ÷ 6; 22 Sep has no entry), `next_tasks` = **2** tasks:
      `16:00 Study: SQL joins` then `19:00 Read 20 pages`.
- [x] `weekly` · `2026-09-26` → scores `80, 50, 100, 75, 50, 100, 60`; moods `4, 3, null, 5, 3, 4, 4`.
- [x] `summary` · `2026-09-19` → `score` 40, **`streak_days` 1** (19th doesn't count yet → 18th counts →
      17th has no tasks and stops it), `avg_mood_7d` **3.1** (22 ÷ 7).
- [x] `weekly` · `2026-09-19` → 13–19 Sep: scores `100, 50, 33, 100, null, 75, 40`; moods `4, 3, 2, 4, 3, 4, 2`.
- [x] `summary` · `2026-09-17` → `tasks_total` 0, `score` **null**, `streak_days` **1** (16th only; 15th is 33%).
- [x] Today stops counting: `POST /api/tasks` twice for `2026-09-26` (any title and time) → 3 of 7 = **43** →
      `streak_days` **6** (from yesterday: 20–25 Sep). `DELETE` both → back to **7**.

## Round 4 — Browser

Log in at http://localhost:5173.

### 4a — Demo (seeded)

- [x] You land on **/dashboard** after logging in. The greeting matches your clock: **before 12:00**
      "Good morning, Demo", **12:00–16:59** "Good afternoon, Demo", **from 17:00** "Good evening, Demo".
      Below it: "Saturday, September 26, 2026".
- [x] Cards: **3 of 5 done**, green bar at 60%, "60%" · **🔥 7 days** · **🙂 Good** · **🙂 3.8 / 5**.
- [x] Next up: **4:00 PM Study: SQL joins** (high) and **7:00 PM Read 20 pages** (low). "Open planner →" goes to /planner.
- [x] Chart: 7 bars (Sun 20 … Today 26); only today's bar has a value on it ("60%"); "Today" is bold indigo.
      Mood panel: amber dots, with **no dot and no line on Tue 22**: the line stops before it and starts again after it.
- [x] Hover a day column → a light highlight and a tooltip with 3 lines, e.g. for Tue 22:
      the date · "Tasks: 3 of 3 done (100%)" · "Mood: no journal entry".
- [x] Under the chart: "Tasks on 7 of 7 days, 74% done on average; best day Tue (100%). Mood logged on 6 of 7 days,
      average 3.8 (Good)."
- [x] "Show as a table" opens a 7-row table with the same information (works with the keyboard: Tab + Enter).
- [x] In the Planner, tick "Study: SQL joins" → back to Dashboard → **4 of 5 done**, 80%, Next up shows only
      "Read 20 pages". Tick it too → 5 of 5, and Next up says **"All done for today 🎉"**. Untick both.
- [x] Add 2 tasks for today in the Planner → Dashboard: **3 of 7 done** (43%), streak **🔥 6 days**.
      Delete them → back to 7 days.

### 4b — User B (a 0% day vs. a no-task day)

- [x] Cards: **No tasks yet** + "Plan your day →" · **Start a streak today!** · **😐 Okay** · **😐 3.0 / 5**.
- [x] Next up: **"Nothing planned for today yet."**
- [x] Chart: Fri 25 has a **thin 2px stub** at the baseline (1 task, 0 done = 0%); every other day says **"no tasks"**
      with no bar. Only one mood dot (today, middle line).

### 4c — Brand-new user

- [x] Register a new user in the browser (e.g. `new@example.com`) → the dashboard shows **no chart**; instead:
      "Your week will show up here once you start planning." with links to the Planner and today's journal.
- [x] Cards: No tasks yet · Start a streak today! · **"Write today's journal →"** (goes to **/journal/2026-09-26**) ·
      "No journal entries in the last 7 days."
- [x] Write today's journal from that link → back to Dashboard: today's mood shows, the average shows, and the
      chart appears (with only a mood dot on Today).

### 4d — Other checks

- [x] Phone width: DevTools → device toolbar → 375 px. Cards stack one per row, the chart fills the width,
      "no tasks" wraps onto two lines, no sideways scrolling inside the dashboard.
- [x] Resize the window → the chart redraws to the new width (text doesn't shrink).
- [x] Network tab: opening the Dashboard makes **2** calls: `summary?date=2026-09-26` and `weekly?end=2026-09-26`,
      both with your **local** date.
- [x] Stop the backend → reload Dashboard → "Can't reach the server. Is the backend running?".
- [x] Log out → go to http://localhost:5173/dashboard → redirected to login.

## Which tests depend on the time of day

| Test | Why | What to expect |
|---|---|---|
| Greeting (4a) | Uses the browser's clock | < 12:00 morning · 12:00–16:59 afternoon · ≥ 17:00 evening |
| `date=2026-09-27` (2d) | Limit is **UTC** today + 1 day | IST before 05:30 → 422 · after 05:30 → 200 |
| Seed script without `--today` | Uses this computer's local date | After midnight it seeds a different 14 days, so always pass `--today 2026-09-26` for the numbers above |
| Dashboard left open past midnight | "Today" is read when the page loads | Reload the page after midnight to see the new day |

**Not** time-dependent: the "today doesn't count yet" rule only looks at the date, not the hour, and
`next_tasks` shows incomplete tasks of the day even if their time has already passed.
