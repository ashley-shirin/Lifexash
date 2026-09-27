# TiDB Cloud Starter: manual test checklist

Status: passed on 2026-09-27 against the real TiDB Starter cluster (AWS Singapore, TiDB v8.5.3-serverless).
The automated check (`verify_remote_db.py`) passed, and so did Rounds 1, 4, 5 and 6. Rounds 2–3 were skipped
(covered by the automated check and Round 4).

Proves that the backend works on the production database, TiDB Cloud Starter (MySQL-compatible, TLS
only), before deploying. It covers:
- the TLS connection
- migrations
- the constraints that behave differently from MySQL (CHECK, FK cascade, UNIQUE, ENUM, collation)
- the app itself
- idle connections
- the local-only backup guard

The backend runs **on your PC** but talks to the cloud database. Commands are PowerShell, run from
`backend/` with the venv active. SQL runs in TiDB Cloud's **SQL Editor** (or any MySQL client with TLS).

**Never put the TiDB password in a file in the project.** It only goes in `$env:DATABASE_URL` for the
current PowerShell window, and later in the host's settings. A real environment variable wins over
`backend/.env`, so your local `.env` stays unchanged.

## Setup

- [x] TiDB Cloud → create a **Starter** cluster (free) in the region closest to where the backend will be hosted.
- [x] SQL Editor, as the cluster's root user:
  ```sql
  CREATE DATABASE lifexash CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
  CREATE USER '<PREFIX>.lifexash_app' IDENTIFIED BY '<a long random password>';
  GRANT ALL PRIVILEGES ON lifexash.* TO '<PREFIX>.lifexash_app';
  ```
  `<PREFIX>` is the cluster's user prefix, shown in the **Connect** dialog (e.g. `abc123XYZ`). Generate the
  password with `python -c "import secrets; print(secrets.token_urlsafe(24))"`, which gives a
  URL-safe password with nothing to encode.
- [x] Turn on CHECK constraints **before** the tables are created (TiDB drops them otherwise):
  ```sql
  SET GLOBAL tidb_enable_check_constraint = ON;
  SELECT @@global.tidb_enable_check_constraint;   -- expect 1
  ```
  Write down the result: ☑ it worked (1) / ☐ refused on Starter. If it was refused, the API's
  Pydantic check (mood 1–5) is the only guard. That's acceptable, but record it under Findings.
- [x] PowerShell, **single quotes**, so a `$` in the password isn't treated as a variable:
  ```powershell
  $env:DATABASE_URL = 'mysql+pymysql://<PREFIX>.lifexash_app:<PASSWORD>@gateway01.<REGION>.prod.aws.tidbcloud.com:4000/lifexash?charset=utf8mb4'
  ```
- [ ] **Host check, in the SAME window, before every other step** (added after Finding 1):
  ```powershell
  python -c "from app.core.database import engine; print(engine.url)"
  ```
  → must show `…@gateway01.<REGION>.prod.aws.tidbcloud.com:4000/lifexash` (the password shows as `***`).
  If it shows `localhost`, the variable isn't set in this window: everything would silently run against
  local MySQL from `backend/.env`. Repeat this check whenever you open a new window.
- [x] **Create the tables** (added after Finding 1: a new cluster starts empty):
  ```powershell
  alembic upgrade head
  alembic current      # → 81878a6609ca (head)
  ```
  Then in the SQL Editor: `USE lifexash; SHOW TABLES;` → the 7 tables.

## Automated check: `scripts/verify_remote_db.py`

Run with `$env:DATABASE_URL` set to TiDB (host check above first): `python -m scripts.verify_remote_db`. It
uses its own test user and deletes it afterwards. Real data is only read. Exit code 0 = all passed. The last
line must say **`on gateway01…:4000, REMOTE database (verified TLS)`**. If it says `LOCAL database`, it
didn't test TiDB.

**Run on TiDB on 2026-09-27**, after `alembic upgrade head`. The output started with
`Database: lifexash on gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000`, server `8.0.11-TiDB-v8.5.3-serverless`,
and ended with "All checks passed." That run used the script version from before the LOCAL/REMOTE last line
was added, so the first line is the proof of the target.

- [x] TLS in use, with the verified certifi settings (server reports a TiDB version and a TLS cipher): `TLS_AES_128_GCM_SHA256`.
- [x] All 7 tables exist, with collation `utf8mb4_0900_ai_ci`. `alembic_version` is at head (`81878a6609ca`).
- [x] mood CHECK constraint: **enforced** (mood 6 rejected with error 3819).
- [x] Deleting a user CASCADE-deletes their tasks, notes, tags, note_tags and journal entries (all 1 → 0).
- [x] utf8mb4: `utf8mb4 check 😀🎉 ñ 日本` saved and read back unchanged.
- [x] Test user removed afterwards.

The manual rounds below are ticked only where the script fully covered them. They also test things
the script doesn't: TiDB refusing unencrypted connections, the certificate hostname check, UNIQUE/ENUM/FK
errors, the app itself, idle connections and the backup guard.

## Round 1: TLS connection (passed 2026-09-27)

- [x] The connection works and is encrypted:
  ```powershell
  @'
  from sqlalchemy import text
  from app.core.database import engine
  with engine.connect() as c:
      print("version:", c.execute(text("SELECT VERSION()")).scalar())
      print("cipher:", c.execute(text("SHOW SESSION STATUS LIKE 'Ssl_cipher'")).all())
      print("time_zone:", c.execute(text("SELECT @@session.time_zone")).scalar())
  '@ | python -
  ```
  → `version` contains **TiDB**, `cipher` is **not empty** (e.g. `TLS_AES_128_GCM_SHA256`), and
  `time_zone` is `+00:00`.
- [x] TiDB itself refuses unencrypted connections. This test turns TLS **off** on purpose:
  ```powershell
  @'
  import pymysql
  from sqlalchemy import make_url
  from app.core.config import settings
  u = make_url(settings.DATABASE_URL)
  try:
      pymysql.connect(host=u.host, port=u.port, user=u.username, password=u.password, ssl_disabled=True)
      print("UNEXPECTED: connected without TLS")
  except pymysql.err.OperationalError as e:
      print("refused as expected:", e.args[1][:120])
  '@ | python -
  ```
  → it prints "refused as expected" (e.g. "Connections using insecure transport are prohibited").
- [x] The certificate check is real. Connect to the gateway's **IP address** with the app's own TLS settings.
      The certificate is for `*.tidbcloud.com`, not for an IP, so the hostname check must reject it:
  ```powershell
  @'
  import socket, pymysql
  from sqlalchemy import make_url
  from app.core.config import settings
  from app.core.database import connect_args_for
  u = make_url(settings.DATABASE_URL)
  ip = socket.gethostbyname(u.host)
  try:
      pymysql.connect(host=ip, port=u.port, user=u.username, password=u.password, connect_timeout=10,
                      **connect_args_for(settings.DATABASE_URL))
      print("UNEXPECTED: connected to", ip)
  except pymysql.err.OperationalError as e:
      print("refused as expected:", str(e.args[1])[:150])
  '@ | python -
  ```
  → "refused as expected", with a certificate error such as "IP address mismatch". "connected" means the check failed.

## Round 2: Table definitions (skipped, covered)

Skipped on 2026-09-27: covered by the automated check (tables, collation, CHECK enforced, cascade) and
Round 4 (cascade through the app). Migrations moved to Setup.

- [ ] `SHOW CREATE TABLE journal_entries;` →
  - `COLLATE=utf8mb4_0900_ai_ci`
  - `UNIQUE KEY ... (user_id, entry_date)`
  - FK `fk_journal_entries_user_id_users` `ON DELETE CASCADE`
  - the CHECK `ck_journal_entries_mood_range`, **only if** the Setup step worked. Record whether it's there.
- [ ] `SHOW CREATE TABLE tasks;` → `priority enum('low','medium','high')` with default `'medium'`, FK with
      `ON DELETE CASCADE`, and index `ix_tasks_user_id_task_date`.
- [ ] `SHOW CREATE TABLE note_tags;` → primary key `(note_id, tag_id)`, and **both** FKs `ON DELETE CASCADE`.
- [ ] `SHOW CREATE TABLE users;` and `SHOW CREATE TABLE tags;` → `uq_users_email`, `uq_tags_user_id_name`.

## Round 3: Constraints (SQL Editor) (skipped, covered)

Skipped on 2026-09-27: UNIQUE was tested through the app in Round 4 (409s), cascade in Round 4 (last
item), and CHECK, cascade and utf8mb4 by the automated check. The ENUM and FK errors (1265, 1452)
were not tested on TiDB. The API validates both before the database sees them.

Uses a throw-away user. Write down its id and type it in as `<N>` below. Session variables like `@u`
may be lost if the editor runs each statement in a new session.

- [ ] Create the test user and look up its id:
  ```sql
  USE lifexash;
  INSERT INTO users (name, email, password_hash) VALUES ('Check', 'check@example.com', 'x');
  SELECT id FROM users WHERE email = 'check@example.com';   -- write this down as <N>
  ```
- [ ] Rows in every child table:
  ```sql
  INSERT INTO tasks (user_id, title, task_date, task_time) VALUES (<N>, 'T', '2026-09-27', '09:00');
  INSERT INTO notes (user_id, title, content) VALUES (<N>, 'N', 'emoji test 😀🎉');
  INSERT INTO tags (user_id, name) VALUES (<N>, 'work');
  INSERT INTO note_tags (note_id, tag_id)
    SELECT n.id, t.id FROM notes n JOIN tags t ON t.user_id = n.user_id WHERE n.user_id = <N>;
  INSERT INTO journal_entries (user_id, entry_date, content, mood) VALUES (<N>, '2026-09-27', 'ok', 4);
  ```
- [ ] Default: `SELECT priority FROM tasks WHERE user_id = <N>;` → `medium`.
- [ ] Emoji: `SELECT content FROM notes WHERE user_id = <N>;` → `emoji test 😀🎉`, not `????`.
- [ ] UNIQUE, case-insensitive (collation `ai_ci`): `INSERT INTO users (name, email, password_hash) VALUES
      ('X', 'CHECK@example.com', 'x');` → **error 1062** Duplicate entry.
- [ ] UNIQUE tag per user: `INSERT INTO tags (user_id, name) VALUES (<N>, 'Work');` → **1062**.
- [ ] One journal entry per day: `INSERT INTO journal_entries (user_id, entry_date, content, mood) VALUES
      (<N>, '2026-09-27', 'again', 3);` → **1062**.
- [ ] ENUM: `INSERT INTO tasks (user_id, title, task_date, task_time, priority) VALUES (<N>, 'E', '2026-09-27',
      '10:00', 'urgent');` → **error** (e.g. 1265 "Data truncated", from strict SQL mode). No row is added.
- [ ] CHECK: `INSERT INTO journal_entries (user_id, entry_date, content, mood) VALUES (<N>, '2026-09-26', 'bad', 6);`
  - if the CHECK exists: **error 3819** (check constraint violated)
  - if it doesn't: the row is **inserted**. Record that under Findings (the API's 422 still protects the app).
- [ ] FK: `INSERT INTO tasks (user_id, title, task_date, task_time) VALUES (999999999, 'F', '2026-09-27',
      '09:00');` → **error 1452** (foreign key fails).
- [ ] Before deleting, note the ids of the child rows that must disappear:
      `SELECT id FROM notes WHERE user_id = <N>;` → `<NOTE>`, and `SELECT id FROM tags WHERE user_id = <N>;` → `<TAG>`.
- [ ] **Cascade:** `DELETE FROM users WHERE id = <N>;`, then:
  ```sql
  SELECT (SELECT COUNT(*) FROM tasks WHERE user_id = <N>) AS tasks,
         (SELECT COUNT(*) FROM notes WHERE user_id = <N>) AS notes,
         (SELECT COUNT(*) FROM tags WHERE user_id = <N>) AS tags,
         (SELECT COUNT(*) FROM journal_entries WHERE user_id = <N>) AS journal,
         (SELECT COUNT(*) FROM note_tags WHERE note_id = <NOTE> OR tag_id = <TAG>) AS note_tags;
  ```
  → all **0**. The `note_tags` row went too, through notes → note_tags and tags → note_tags.

## Round 4: The app against TiDB (passed 2026-09-27)

Same PowerShell window (`$env:DATABASE_URL` still set): `uvicorn app.main:app --reload`. Second window:
`npm run dev` in `frontend/`.

- [x] <http://localhost:8000/api/health> → `{"status":"ok"}`.
- [x] Register **User A** and **User B** in the browser. Registering A's email again, in capitals, →
      "email already registered" (409).
- [x] As A: add, edit, toggle and delete tasks. Notes with tags: create a tag inline, filter by it,
      search, pin. Create the same tag again → 409 message. Journal: write today's entry.
- [x] Swagger, as A: `POST /api/journal` for a day that already has an entry → **409**. Mood `6` → **422**.
- [x] Timestamps: after editing a note it shows "updated just now", and the JSON `updated_at` ends in `Z`
      and matches the current UTC time.
- [x] IDOR spot check: as B, `GET /api/notes/{A's note id}` and `DELETE /api/tasks/{A's task id}` → **404**.
- [x] Dashboard sums: `python -m scripts.seed_demo <A's email> --yes`, then check the dashboard shows
      **3 of 5** done today, score **60** and a streak of **7**. These numbers assume an **empty** account:
      seed_demo skips days that already have tasks or a journal entry (Finding 3), so use a freshly
      registered user. This is the `SUM()` bug from the dashboard
      checklist, now checked on TiDB.
- [x] Ids: in Swagger, look at the `id` of the tasks you created. Gaps or jumps (e.g. 1, 2, 30001) are
      **expected** on TiDB and must not break anything. The planner's order is by time, not id.
- [x] Log in as A, then delete A's account in the SQL Editor (`DELETE FROM users WHERE email = '...'`) →
      the next action in the browser logs you out (401). No rows are left in any table for A's id.

## Round 5: Idle connections (passed 2026-09-27)

- [x] Leave the backend running and do nothing for **at least 10 minutes**. That's longer than
      `pool_recycle` (5 min), and long enough for the cluster to close idle connections.
- [x] Reload the dashboard → it loads on the **first** try. There's no 500 error, and no
      "Lost connection" / "MySQL server has gone away" in the uvicorn log.
- [ ] Optional (not run), the next day: the first request after a long idle time may be slow (the cluster
      is waking up) but must succeed.

## Round 6: Backup scripts refuse the cloud database (passed 2026-09-27)

- [x] `python -m scripts.backup_db` → stops with "DATABASE_URL points at gateway01…, not a local MySQL". No
      file is created in `Documents\LifeXash-backups`.
- [x] `python -m scripts.restore_test` → the same error. No `lifexash_restore_test` database appears on TiDB
      (`SHOW DATABASES;`).

## Clean-up

- [x] Delete the test accounts (User A, User B, the demo data) in the SQL Editor, unless you want to keep them
      as the production demo.
- [ ] `Remove-Item Env:DATABASE_URL`, or close the PowerShell window. Then `alembic current` and a page load
      in the app use the **local** MySQL again.
- [ ] `git status` → no file contains the TiDB host or password (`git grep -n tidbcloud` shows only
      docs, `.env.example` and the README, all with placeholders).

## Findings

Record anything that behaved differently from the expected results above.

1. **The `lifexash` database on TiDB had no tables until `alembic upgrade head` was run by hand**, even though an
   earlier `verify_remote_db.py` run had been reported as "all checks passed" on TiDB.
   - **Cause (most likely):** that run went to **local MySQL**. On an empty TiDB database the script prints
     `[FAIL] Tables exist … missing` and stops (exit 1), so it can't have passed there. Its results
     (7 tables at head, CHECK enforced) match local MySQL exactly. `DATABASE_URL` was probably not
     set in *that* PowerShell window (a different or reopened window), so `backend/.env` was used. The output
     showed it (`Database: … on localhost:3306`, `[INFO] Local database: …`), but only the summary was passed on.
   - **Actions:**
     - Setup now starts with a host check and `alembic upgrade head`.
     - `verify_remote_db.py` now names the database and LOCAL/REMOTE in its final line.
     - The script was then re-run against TiDB (after `alembic upgrade head`), and every check passed there
       (see the automated check section).
2. **`seed_demo` said "Would add N tasks …" and then "Done." on a real run.** Fixed: a real run now prints
   "Added N tasks and M journal entries." only after the commit. "Would add …" is kept for the dry run
   (without `--yes`). There's a unit test in `tests/test_seed_demo.py`.
3. **`seed_demo` skips days that already have data**, so on a non-empty account the dashboard doesn't show 3 of 5 /
   60 / streak 7. The Round 4 note now says the numbers assume an empty account, and the script prints a
   note when it skips days.
4. **The CHECK constraint is enforced on TiDB Starter**, provided `SET GLOBAL tidb_enable_check_constraint = ON`
   is set **before** `alembic upgrade head`. `verify_remote_db.py` on TiDB: mood 6 was rejected with error 3819,
   the same as on local MySQL.
