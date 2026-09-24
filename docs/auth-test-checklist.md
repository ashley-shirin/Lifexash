# Auth — manual test checklist

Status: **not run yet.** Tick each box as it passes; note anything that fails.

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

- [ ] `POST /api/auth/register` with `{"name":"Test","email":"Test@Example.com","password":"password123"}` → **201**; response has id, name, `email` lowercased (`test@example.com`), created_at, and **no** `password_hash`.
- [ ] Register the same email again (even as `TEST@example.com`) → **409** "Email is already registered".
- [ ] Register with a 7-character password → **422**.
- [ ] Register with email `notanemail` → **422**.
- [ ] Register with name `"   "` → **422**.
- [ ] `POST /api/auth/login` with correct details → **200** with `access_token` and `token_type: "bearer"`.
- [ ] Login with right email + wrong password → **401** "Invalid email or password".
- [ ] Login with an email that doesn't exist → **401** with the **exact same** message.
- [ ] `GET /api/auth/me` without authorizing → **401** "Not authenticated".
- [ ] Click **Authorize**, paste just the token (no "Bearer" prefix), then `GET /me` → **200** with your user.
- [ ] Authorize with the token with one character changed → `/me` → **401**.
- [ ] In MySQL Workbench: `SELECT email, password_hash FROM users;` → hash starts with `$2b$`, the plain password appears nowhere.

## Browser (http://localhost:5173)

- [ ] Logged out, visit `/profile` → redirected to `/login`.
- [ ] Visit `/` → ends up at `/login` (via `/dashboard`).
- [ ] Submit empty login form → "Email is required." / "Password is required." shown; nothing sent (check DevTools → Network).
- [ ] Register with mismatched passwords or a short password → field error shown under the input.
- [ ] Register with an already-used email → red "Email is already registered" box.
- [ ] Register successfully → button shows "Creating account…", then you land on `/dashboard` and the navbar shows the app links.
- [ ] Login with wrong password → red "Invalid email or password"; button re-enabled; no page reload.
- [ ] Login successfully → `/dashboard`.
- [ ] DevTools → Network → any API call has the header `Authorization: Bearer …`.
- [ ] Refresh the page → still logged in.
- [ ] While logged in, visit `/login` → bounced to `/dashboard`.
- [ ] Profile page shows your name + email; click **Log out** → `/login`, and `lifexash_token` is gone from DevTools → Application → Local Storage.
- [ ] **Expired/invalid token:** while logged in, edit `lifexash_token` in Local Storage to junk, then refresh → sent to `/login` with "Your session has expired…".
- [ ] **Backend down:** stop uvicorn, try to log in → "Can't reach the server. Is the backend running?"
