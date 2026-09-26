# Notes + Tags — manual test checklist

Status: all rounds passed (2026-09-26).

Change after testing: the search debounce was raised from 300 ms to 500 ms, and the list now cancels the
previous search request (AbortController), so an older response can never overwrite a newer one.

## Setup

No migration needed — the `notes`, `tags` and `note_tags` tables already exist from the initial migration.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload       # http://localhost:8000/docs
```

Second terminal: `cd frontend` → `npm run dev` (http://localhost:5173).

You need **two users** (the same ones as the tasks checklist):
- **User A**: `a@example.com` / `password123`
- **User B**: `b@example.com` / `password123`

In Swagger, log in as A, copy the `access_token`, click **Authorize** and paste it.

## Round 1 — Swagger: tags (as User A)

- [x] `POST /api/tags` `{"name":"  Study  "}` → **201**, name saved as `"Study"` (trimmed). Note the `id` (call it **TA1**).
- [x] `POST /api/tags` `{"name":"work"}` → **201**. Note the `id` (**TA2**).
- [x] `POST /api/tags` `{"name":"study"}` → **409** "Tag already exists" (names are case-insensitive).
- [x] `{"name":"STUDY"}` → **409**.
- [x] `{"name":"   "}` → **422** "Tag name cannot be blank".
- [x] Name with 51 characters → **422**.
- [x] `GET /api/tags` → **200**, both tags, sorted by name: `Study`, `work`.

## Round 2 — Swagger: create notes + validation (as User A)

- [x] `POST /api/notes` `{"title":"Exam prep","content":"Revise chapter_1, aim for 100%","tag_ids":[TA1]}` → **201**;
      `is_pinned` false, `tags` = `[{"id":TA1,"name":"Study"}]`. Note the `id` (**N1**).
- [x] `{"title":"Groceries","content":"milk, eggs","tag_ids":[TA2]}` → **201** (**N2**).
- [x] `{"title":"Quick idea","content":""}` → **201**, `tags` is `[]` (empty content is allowed; tag_ids is optional) (**N3**).
- [x] `{"title":"Dupes","content":"x","tag_ids":[TA1,TA1]}` → **201** with `Study` only **once**. Then `DELETE` this note.
- [x] Leave out `content` → **422** (content is required).
- [x] `"title":"   "` → **422** "Title cannot be blank".
- [x] Title with 201 characters → **422**.
- [x] `"tag_ids":[999999]` → **404** "Tag not found" — and no note was created (check `GET /api/notes`).
- [x] `"title":"  Padded  "` → **201**, title saved as `"Padded"`. Delete it again.

## Round 3 — Swagger: list, search, filter, sort

- [x] `GET /api/notes` → newest updated first: N3, N2, N1. Each note has its `tags` array.
- [x] `?q=exam` → only N1 (**case-insensitive**, title match).
- [x] `?q=EGGS` → only N2 (content match).
- [x] `?q=100%` → only N1. `?q=%` → only N1 (it's the only note containing a `%` character).
- [x] `?q=chapter_` → N1. `?q=_` → only N1 (`_` is treated as a normal character, not "any one character").
- [x] `?q=zzz` → **200** with `[]`.
- [x] `?tag_id=TA2` → only N2.
- [x] `?q=milk&tag_id=TA1` → `[]` (both filters must match).
- [x] `?tag_id=999999` → **404** "Tag not found".

## Round 4 — Swagger: get / update / pin / delete

- [x] `GET /api/notes/{N1}` → **200** with tags. `GET /api/notes/999999` → **404** "Note not found".
- [x] `PUT /api/notes/{N1}` `{"title":"Final exam prep"}` → **200**; title changed, content/tags/pin **unchanged**, `updated_at` is newer.
- [x] `PUT /api/notes/{N1}` `{"tag_ids":[TA1,TA2]}` → both tags; title unchanged; `updated_at` is newer (a tags-only change counts as an update).
- [x] `PUT /api/notes/{N1}` `{"tag_ids":[]}` → `tags: []`. Put `[TA1]` back.
- [x] `PUT` `{"title":null}` → **422**. `{"content":null}` → **422**. `{"tag_ids":null}` → **422**.
- [x] `PUT` `{"tag_ids":[999999]}` → **404**, and N1's tags are **unchanged**.
- [x] Write down N2's `updated_at`. `PATCH /api/notes/{N2}/pin` → `is_pinned: true`, and `updated_at` is **the same as before** (pinning isn't an edit).
- [x] `GET /api/notes` → **N2 first** (pinned), then the rest by `updated_at`.
- [x] `PATCH /api/notes/{N2}/pin` again → `is_pinned: false`. Pin it again for the next rounds.
- [x] Click **Authorize → Logout**, then `GET /api/notes` → **401**. Authorize as A again.

## Round 5 — Swagger: User B can't see or use A's notes and tags

Log in as **B**, Authorize with B's token.

- [x] `GET /api/notes` → `[]`. `GET /api/tags` → `[]`.
- [x] `POST /api/tags` `{"name":"Study"}` → **201** (tag names are unique **per user**, so B can reuse A's name). Note it (**TB1**).
- [x] `GET /api/notes/{N1}` → **404** "Note not found" (the same as a note that doesn't exist, **not** 403).
- [x] `PUT /api/notes/{N1}` `{"title":"hacked"}` → **404**.
- [x] `PATCH /api/notes/{N1}/pin` → **404**.
- [x] `DELETE /api/notes/{N1}` → **404**.
- [x] `DELETE /api/tags/{TA1}` → **404** "Tag not found".
- [x] `GET /api/notes?tag_id=TA1` → **404** "Tag not found".
- [x] **Attach A's tag to B's note (create):** `POST /api/notes` `{"title":"B note","content":"b","tag_ids":[TA1]}` → **404** "Tag not found", and no note is created.
- [x] **Mixed tags:** `{"title":"B note","content":"b","tag_ids":[TB1,TA1]}` → **404** (one foreign tag is enough to reject everything).
- [x] `POST /api/notes` `{"title":"B note","content":"b","tag_ids":[TB1]}` → **201** (**NB1**).
- [x] **Attach A's tag to B's note (update):** `PUT /api/notes/{NB1}` `{"tag_ids":[TA1]}` → **404**; `GET /api/notes/{NB1}` still has only TB1.
- [x] `?q=exam` → `[]` (search never finds A's notes).
- [x] Authorize as **A** again → N1 still exists, title **not** "hacked", tag `Study` (TA1) still exists; A's `GET /api/tags` does **not** show B's tag.

## Round 6 — Swagger: deleting a tag keeps the notes

As **A**:

- [x] Make sure N1 has TA1. `DELETE /api/tags/{TA1}` → **204**.
- [x] `GET /api/notes/{N1}` → **200**, the note is still there, its `tags` no longer include `Study`.
- [x] `GET /api/tags` → only `work`.
- [x] `POST /api/tags` `{"name":"Study"}` → **201** (the name is free again).
- [x] `DELETE /api/tags/{TA1}` again → **404**.
- [x] `DELETE /api/notes/{N3}` → **204**; `GET /api/notes/{N3}` → **404**.

## Round 7 — Browser: notes list (log in as A)

- [x] Open **Notes** in the navbar. Pinned notes come first with a yellow border and a coloured 📌; the others are sorted by most recently updated.
- [x] Each card shows the title, a **2-line** content preview (write a long note to check it's cut off with "…"), its tags and "updated … ago".
- [x] Click the 📌 on an unpinned note → it jumps to the top, **without** opening the note. Its "updated … ago" text doesn't change. Refresh → it's still pinned.
- [x] Click anywhere else on a card → the editor opens for that note.
- [x] Type `exam` in the search box: the list updates only after you **stop typing** (DevTools → Network shows one `/notes?q=exam` request, not one per letter).
- [x] The URL becomes `/notes?q=exam`. Refresh (F5) → the search text and results are still there.
- [x] Search `zzz` → "No notes match your search."
- [x] Clear the search → all notes come back.
- [x] Click a tag chip → only notes with that tag; the chip is highlighted and the URL has `?tag=…`. Click it again (or **All**) → the filter is removed.
- [x] Tag filter + search together narrow the list further.
- [x] Click **×** on a tag chip → a confirm appears. **Cancel** → nothing changes. **OK** → the chip disappears and the tag is gone from the note cards, but the notes are still there.
- [x] Log in as a **brand-new user** (register C) → Notes shows "No notes yet. Write your first one!" and no tag chips.

## Round 8 — Browser: note editor

- [x] **+ New note** → `/notes/new` with an empty form, cursor in Title.
- [x] Click **Create note** with an empty title → "Title is required." and no request is sent.
- [x] Tag picker: click an existing tag → it gets a ✓ and is highlighted. Click again → unselected.
- [x] Type `Reading` in "New tag name" and press **Enter** → the tag is created and selected; the note is **not** saved yet (you're still on the form).
- [x] Type `reading` (lowercase) and click **Add tag** → no new tag; the existing `Reading` is simply selected.
- [x] Tick "Pin this note", fill in title + content, **Create note** → back on `/notes`; the note is at the top, pinned, with its tags.
- [x] Open it again → the form shows the saved title, content, tags and pin state. Change the content and **Save changes** → it moves to the top of the unpinned notes (or pinned, if pinned) with "updated just now".
- [x] Open a note, unselect all tags, save → the card shows no tags.
- [x] **Cancel** / **← Back to notes** → back to the list, nothing saved.
- [x] **Delete** → a confirm appears. **Cancel** → nothing happens. **OK** → back on `/notes`, the note is gone.
- [x] Stop the backend (Ctrl+C) and click **Save changes** → a red "Can't reach the server" message, no crash. Restart the backend.

## Round 9 — Browser: another user's note is "not found"

- [x] As **A**, open one of A's notes and copy its URL, e.g. `/notes/12`.
- [x] Log out, log in as **B**, paste that URL → **"Note not found"** with a link back — no crash, no data from A's note.
- [x] As B, `/notes/999999` → "Note not found". `/notes/abc` → "Note not found".
- [x] As B, the Notes page shows only B's notes and only B's tag chips (B's `Study`, not A's).
- [x] As B, open `/notes?tag=<A's tag id>` → the list is empty with a red "Tag not found" message, no crash.

## Known limitation

"updated … ago" reads the backend time as your **browser's local time**. MySQL stores it in the DB machine's
local time, so it's correct while both run on your PC. With the DevTools time-zone override from the tasks
checklist (Kiritimati), the "ago" text will be off by the time-zone difference — that's expected for now.

**Fixed (pre-deploy):** timestamps are now stored in UTC and sent with a "Z", so "updated … ago" is correct in
any time zone. See `docs/pre-deploy-checklist.md`, Round 1.
