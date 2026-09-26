# Journal — manual test checklist

Status: all rounds passed (2026-09-26).

The dates below are for testing on **Saturday 26 September 2026** (India, UTC+5:30). If you test on another
day, shift every date by the same number of days.

## Setup

No migration needed — the `journal_entries` table already exists from the initial migration
(with `UNIQUE(user_id, entry_date)` and `CHECK (mood BETWEEN 1 AND 5)`).

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload       # http://localhost:8000/docs
```

Second terminal: `cd frontend` → `npm run dev` (http://localhost:5173).

Users (the same ones as the other checklists):
- **User A**: `a@example.com` / `password123`
- **User B**: `b@example.com` / `password123`

In Swagger, log in as A, copy the `access_token`, click **Authorize** and paste it.

Moods: 1 😞 Awful · 2 🙁 Bad · 3 😐 Okay · 4 🙂 Good · 5 😄 Great

## Round 1 — Swagger: create + validation (as User A)

- [x] `POST /api/journal` → **201**, `title` is `null`. Note the `id` (**J1**).
      ```json
      {"entry_date":"2026-09-26","mood":4,"content":"Finished the notes feature!"}
      ```
- [x] Yesterday is allowed → **201**, title saved as `"Lazy Friday"` (trimmed). Note the `id` (**J2**).
      ```json
      {"entry_date":"2026-09-25","mood":5,"title":"  Lazy Friday  ","content":"Slept in, then a long walk."}
      ```
- [x] Older past date → **201** (**J3**).
      ```json
      {"entry_date":"2026-09-01","mood":2,"title":"Rainy start","content":"Tired all day."}
      ```
- [x] Last month → **201** (**J4**). This one must **not** show up in September.
      ```json
      {"entry_date":"2026-08-31","mood":3,"content":"End of August."}
      ```
- [x] Blank title becomes null → **201**, `title` is `null`. Then `DELETE /api/journal/{id}` this entry.
      ```json
      {"entry_date":"2026-09-10","mood":3,"title":"   ","content":"Blank title test"}
      ```
- [x] **Same day again** → **409** "An entry for this date already exists" (and J1 is unchanged).
      ```json
      {"entry_date":"2026-09-26","mood":1,"content":"Second entry today"}
      ```
- [x] Two days ahead → **422** "entry_date cannot be in the future".
      ```json
      {"entry_date":"2026-09-28","mood":3,"content":"Too early"}
      ```
- [x] Tomorrow (the 1-day tolerance). The limit is **UTC today + 1 day**, so in India:
      **after 05:30** → **201** (then `DELETE` it again); **before 05:30** → **422** (UTC is still on the 25th).
      ```json
      {"entry_date":"2026-09-27","mood":3,"content":"Tolerance test"}
      ```
- [x] Mood 0 → **422** "Input should be greater than or equal to 1".
      ```json
      {"entry_date":"2026-09-11","mood":0,"content":"x"}
      ```
- [x] Mood 6 → **422** "Input should be less than or equal to 5".
      ```json
      {"entry_date":"2026-09-11","mood":6,"content":"x"}
      ```
- [x] Mood as text → **422** "Input should be a valid integer" (strict: `"3"` is not a number).
      ```json
      {"entry_date":"2026-09-11","mood":"3","content":"x"}
      ```
- [x] Mood missing → **422** "Field required".
      ```json
      {"entry_date":"2026-09-11","content":"x"}
      ```
- [x] Blank content → **422** "Content cannot be blank".
      ```json
      {"entry_date":"2026-09-11","mood":3,"content":"   "}
      ```
- [x] Content missing → **422** "Field required".
      ```json
      {"entry_date":"2026-09-11","mood":3}
      ```
- [x] Title with 201 characters → **422** "String should have at most 200 characters".
      ```json
      {"entry_date":"2026-09-11","mood":3,"title":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","content":"x"}
      ```
- [x] Invalid date → **422** (e.g. 31 September doesn't exist).
      ```json
      {"entry_date":"2026-09-31","mood":3,"content":"x"}
      ```
- [x] After all these, `GET /api/journal?month=2026-09` shows only J3, J2, J1 — none of the failed requests created an entry.

## Round 2 — Swagger: month list + get by date

- [x] `GET /api/journal?month=2026-09` → **200**, exactly **J3, J2, J1** in that order (sorted by date), **not** J4.
- [x] `?month=2026-08` → only J4.
- [x] `?month=2026-10` → `[]`.
- [x] Bad month formats → **422** each: `2026-13`, `2026-00`, `2026-9`, `09-2026`, `abc`, `2026-09-01`.
- [x] No `month` at all → **422** "Field required".
- [x] `GET /api/journal/date/2026-09-25` → **200**, that's J2.
- [x] `GET /api/journal/date/2026-09-20` → **404** "No journal entry for this date".
- [x] `GET /api/journal/date/2026-13-45` → **422**. `GET /api/journal/date/abc` → **422**.

## Round 3 — Swagger: update + delete (as A)

- [x] `PUT /api/journal/{J1}` → **200**; mood is 5, title and content **unchanged**, `updated_at` is newer.
      ```json
      {"mood":5}
      ```
- [x] `PUT /api/journal/{J1}` → **200**; title is `"Good day"` (trimmed).
      ```json
      {"title":"  Good day  "}
      ```
- [x] `PUT /api/journal/{J1}` → **200**; title is back to `null` (null clears the title).
      ```json
      {"title":null}
      ```
- [x] `PUT /api/journal/{J1}` → **200**; title is `null` (blank also clears it).
      ```json
      {"title":"   "}
      ```
- [x] `PUT /api/journal/{J1}` → **200**; all three fields change.
      ```json
      {"mood":4,"title":"Notes done","content":"Finished the notes feature and started the journal."}
      ```
- [x] Explicit null mood → **422** "Mood cannot be null".
      ```json
      {"mood":null}
      ```
- [x] Explicit null content → **422** "Content cannot be null".
      ```json
      {"content":null}
      ```
- [x] Blank content → **422** "Content cannot be blank".
      ```json
      {"content":"   "}
      ```
- [x] Mood out of range → **422**.
      ```json
      {"mood":7}
      ```
- [x] **Changing the date is not allowed** → **422** "Extra inputs are not permitted", and J1 is still on 26 Sep.
      ```json
      {"entry_date":"2026-09-20"}
      ```
- [x] `PUT /api/journal/999999` with `{"mood":3}` → **404** "Journal entry not found".
- [x] `DELETE /api/journal/{J3}` → **204**. `GET /api/journal/date/2026-09-01` → **404**. `DELETE /api/journal/{J3}` again → **404**.
- [x] `POST` 1 Sep again → **201** (the day is free after deleting). Note the new id (**J5**).
      ```json
      {"entry_date":"2026-09-01","mood":2,"title":"Rainy start","content":"Tired all day."}
      ```
- [x] Click **Authorize → Logout**, then `GET /api/journal?month=2026-09` → **401**. Authorize as A again.

## Round 4 — Swagger: User B can't see or use A's entries

Log in as **B**, Authorize with B's token.

- [x] `GET /api/journal?month=2026-09` → `[]`.
- [x] `GET /api/journal/date/2026-09-26` → **404** (A has an entry that day, B doesn't — B can't tell).
- [x] `PUT /api/journal/{J1}` → **404** "Journal entry not found" (the same as a missing entry, **not** 403).
      ```json
      {"content":"hacked"}
      ```
- [x] `DELETE /api/journal/{J1}` → **404**.
- [x] B can write on **the same day as A** → **201** (the date is unique **per user**). Note it (**JB1**).
      ```json
      {"entry_date":"2026-09-26","mood":3,"content":"B's day"}
      ```
- [x] Authorize as **A** again → `GET /api/journal/date/2026-09-26` is still J1, content **not** "hacked";
      `?month=2026-09` shows only A's entries (J5, J2, J1), not JB1.

## Round 5 — Browser: month view (log in as A)

- [x] Click **Journal** in the navbar → heading "September 2026", a grid with **Mon … Sun** columns;
      1 Sep is in the **Tuesday** column.
- [x] 1 Sep shows 🙁, 25 Sep shows 😄, 26 Sep shows 🙂. Days with an entry have a light-blue background.
- [x] Today (26 Sep) has a thick blue border and a bold number.
- [x] 27–30 Sep are grey; hovering shows a "not allowed" cursor and clicking does nothing.
- [x] Under the calendar: **"Average mood this month: 🙂 3.7 (3 entries)"** ((2 + 5 + 4) / 3 = 3.67).
- [x] **← Prev** → "August 2026", the URL is `/journal?month=2026-08`, only 31 Aug has 😐, and
      "Average mood this month: 😐 3.0 (1 entry)" (singular "entry").
- [x] **← Prev** again → July: "No entries this month yet."
- [x] Refresh (F5) → still July. **This month** → back to September; the button is disabled while on September.
- [x] **Next →** is disabled on September (later months only have future days).
- [x] Open `/journal?month=2026-13` or `/journal?month=abc` → the current month is shown, no crash.
- [x] Log in as a **brand-new user** (register C) → the grid has no emojis and "No entries this month yet."

## Round 6 — Browser: editor

- [x] Click **24 Sep** (no entry) → `/journal/2026-09-24`, heading "Thursday, 24 September 2026", "No entry for this day yet.",
      no mood selected, empty fields, **no Delete button**.
- [x] Click **Save** with nothing filled in → "Pick a mood." and "Write something about your day.", no request sent
      (DevTools → Network).
- [x] Click 😐 → it gets a blue border and background; the others look faded. Click 😄 → only 😄 is highlighted now.
- [x] Type content only (leave Title empty), **Save** → back on `/journal?month=2026-09`, 24 Sep shows 😄 and the
      average is updated to 4.0 (4 entries).
- [x] Click **24 Sep** again → "Edit your entry for this day.", 😄 selected, content filled in, a **Delete** button.
- [x] Change the mood to 🙁, add a title, **Save** → the calendar shows 🙁 on 24 Sep.
- [x] Open it again, clear the title, **Save** → saved (title is optional; Swagger shows `"title": null`).
- [x] Content only spaces → "Write something about your day.", nothing saved.
- [x] **Cancel** / **← Back to journal** → back to September, nothing changed.
- [x] **Delete** → a confirm appears. **Cancel** → nothing happens. **OK** → back on the calendar, 24 Sep has no emoji.
- [x] Clicking a day in **August** and saving takes you back to **August** (not the current month).
- [x] **409 from the browser:** open `/journal/2026-09-23` in **two tabs**. Save an entry in tab 1. In tab 2, pick a mood,
      write something and Save → red "An entry for this date already exists. Reload the page to edit it."
      Reload tab 2 → it now edits tab 1's entry.
- [x] Stop the backend (Ctrl+C) and click **Save** → a red "Can't reach the server" message, no crash. Restart the backend.

## Round 7 — Browser: bad URLs and another user's data

- [x] `/journal/abc` → **"Invalid date"** with a link back, no crash.
- [x] `/journal/2026-13-45` → "Invalid date". `/journal/2026-02-30` → "Invalid date". `/journal/2026-9-5` → "Invalid date".
- [x] `/journal/2026-09-30` (future) → "This day hasn't happened yet", no form.
- [x] Log out, log in as **B**, open `/journal/2026-09-25` (A has an entry that day) → an **empty form**
      ("No entry for this day yet.") — none of A's text is shown.
- [x] As B, September shows only B's 26 Sep entry (😐) and "Average mood this month: 😐 3.0 (1 entry)".

## Round 8 — Browser: local date, not UTC

The calendar's "today" comes from the browser's **local** date (no `toISOString()`).

- [x] Chrome DevTools (F12) → **⋮ → More tools → Sensors** → Location: **Other…** → Timezone ID `Pacific/Kiritimati`
      (UTC+14). Reload `/journal`.
      After **15:30 IST** it's already **27 Sep** in Kiritimati: 27 Sep is highlighted as today and clickable.
- [x] Still in Kiritimati (and after 15:30 IST), write an entry for 27 Sep and Save → it works. This is the backend's
      1-day tolerance: UTC is on the 26th, and the limit is 26 + 1 = 27.
- [x] Delete that 27 Sep entry again (otherwise it stays in the DB as a "future" day for India).
- [x] Reset Sensors → Location to **No override**.

## Why catch IntegrityError instead of only checking first

If two requests for the same day arrive at the same moment (double-click, two tabs), both can run "is there an entry?"
and both see "no" before either has inserted. Then both INSERT. Only the database's UNIQUE(user_id, entry_date) key
is checked atomically, so the second INSERT fails with an IntegrityError, which the service turns into **409**.
