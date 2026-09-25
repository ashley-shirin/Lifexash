# Auth — manual test checklist

Status: **all 26 tests passed** (2026-09-25).

## Setup

`backend/.env` does not exist yet — create it from the template:

```powershell
cd backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the printed value into `JWT_SECRET` and put your MySQL password into `DATABASE_URL`. Then:

```powershell
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload       # backend on http://localhost:8000
```

In a second terminal: `cd frontend` → `npm run dev` (http://localhost:5173).

## Swagger (http://localhost:8000/docs)

- [x] `POST /api/auth/register` with `{"name":"Test","email":"Test@Example.com","password":"password123"}` → **201**; response has id, name, `email` lowercased (`test@example.com`), created_at, and **no** `password_hash`.
- [x] Register the same email again (even as `TEST@example.com`) → **409** "Email is already registered".
- [x] Register with a 7-character password → **422**.
- [x] Register with email `notanemail` → **422**.
- [x] Register with name `"   "` → **422**.
- [x] `POST /api/auth/login` with correct details → **200** with `access_token` and `token_type: "bearer"`.
- [x] Login with right email + wrong password → **401** "Invalid email or password".
- [x] Login with an email that doesn't exist → **401** with the **exact same** message.
- [x] `GET /api/auth/me` without authorizing → **401** "Not authenticated".
- [x] Click **Authorize**, paste just the token (no "Bearer" prefix), then `GET /me` → **200** with your user.
- [x] Authorize with the token with one character changed → `/me` → **401**.
- [x] In MySQL Workbench: `SELECT email, password_hash FROM users;` → hash starts with `$2b$`, the plain password appears nowhere.

## Browser (http://localhost:5173)

- [x] Logged out, visit `/profile` → redirected to `/login`.
- [x] Visit `/` → ends up at `/login` (via `/dashboard`).
- [x] Submit empty login form → "Email is required." / "Password is required." shown; nothing sent (check DevTools → Network).
- [x] Register with mismatched passwords or a short password → field error shown under the input.
- [x] Register with an already-used email → red "Email is already registered" box.
- [x] Register successfully → button shows "Creating account…", then you land on `/dashboard` and the navbar shows the app links.
- [x] Login with wrong password → red "Invalid email or password"; button re-enabled; no page reload.
- [x] Login successfully → `/dashboard`.
- [x] DevTools → Network → any API call has the header `Authorization: Bearer …`.
- [x] Refresh the page → still logged in.
- [x] While logged in, visit `/login` → bounced to `/dashboard`.
- [x] Profile page shows your name + email; click **Log out** → `/login`, and `lifexash_token` is gone from DevTools → Application → Local Storage.
- [x] **Expired/invalid token:** while logged in, edit `lifexash_token` in Local Storage to junk, then refresh → sent to `/login` with "Your session has expired…".
- [x] **Backend down:** stop uvicorn, try to log in → "Can't reach the server. Is the backend running?"
