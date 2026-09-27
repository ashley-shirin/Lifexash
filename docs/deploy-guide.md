# Deploy guide: Render + TiDB Cloud

How LifeXash goes live:
- **Backend:** FastAPI as a Render web service (free plan, region Singapore)
- **Frontend:** a Render static site, served from Render's global CDN
- **Database:** TiDB Cloud Starter (AWS Singapore)

Everything Render needs is in [`render.yaml`](../render.yaml) (a **Blueprint**: the deployment
described as code). Secrets are never in the repo. You type them into the Render dashboard once.

```
Browser ──HTTPS──▶ lifexash-web (static, CDN)      React build + service worker
   │
   └──HTTPS──▶ lifexash-api (Singapore) ──TLS (verified)──▶ TiDB Starter (Singapore)
               alembic upgrade head && uvicorn
```

## 0. Before you start

- [ ] TiDB is ready: `lifexash` exists and is at head, and `verify_remote_db.py` ends with
      `… REMOTE database (verified TLS).` (see the TiDB checklist, Finding 1).
- [ ] `main` on GitHub has everything: `git status` is clean and `git log origin/main -1` matches your last commit.
- [ ] A Render account, connected to your GitHub account (Render → Account settings → GitHub).
- [ ] A **new** JWT secret for production. Don't reuse the local one:
      `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Keep it in your password manager.
- [ ] The TiDB `DATABASE_URL` for the **`lifexash_app`** user (not root). Special characters in the password
      must be URL-encoded (`python -c "from urllib.parse import quote_plus; print(quote_plus('...'))"`).

## 1. Create the Blueprint

1. Render Dashboard → **New → Blueprint** → pick the `Lifexash` repo, branch `main`.
2. Render reads `render.yaml` and lists **lifexash-api** (web service, Singapore, free) and
   **lifexash-web** (static site).
3. It asks for every `sync: false` variable. The URLs are the ones Render will give the services
   (`https://<service name>.onrender.com`):

   | Service | Variable | Value |
   |---------|----------|-------|
   | lifexash-api | `DATABASE_URL` | `mysql+pymysql://<PREFIX>.lifexash_app:<PASSWORD>@gateway01.<REGION>.prod.aws.tidbcloud.com:4000/lifexash?charset=utf8mb4` |
   | lifexash-api | `JWT_SECRET` | the new secret from step 0 |
   | lifexash-api | `CORS_ORIGINS` | `https://lifexash-web.onrender.com` (no trailing `/`) |
   | lifexash-web | `VITE_API_URL` | `https://lifexash-api.onrender.com/api` |

4. **Apply**. Render creates both services and starts the first deploys.

If a name is taken, Render adds a suffix (e.g. `lifexash-web-a1b2.onrender.com`). Check the real
URLs at the top of each service's page. If they differ from what you entered, go to step 3.

## 2. Watch the first deploy

**lifexash-api → Logs**, in this order:
1. `pip install -r requirements.txt` → `Successfully installed …`
2. `Context impl MySQLImpl` / `Will assume non-transactional DDL`: Alembic connected to TiDB over TLS.
   There's no "Running upgrade" line, because the database is already at head.
3. `Uvicorn running on http://0.0.0.0:10000` → the health check passes → **Live**.

A failed migration or database connection stops at step 2. Uvicorn never starts, the deploy fails and the
previous version keeps running. `/api/health` itself doesn't touch the database. It only says the server is up.

**lifexash-web → Logs**: `npm ci`, then `vite build`, then `PWA … precache 10 entries` → **Live**. If the build
says `VITE_API_URL is missing`, the variable wasn't set. That's our own check in `vite.config.js`.

## 3. Fix the URLs (only if Render added a suffix)

- lifexash-api → Environment → `CORS_ORIGINS` = the real static-site URL → Save. Render redeploys the API.
- lifexash-web → Environment → `VITE_API_URL` = the real API URL + `/api` → Save, then
  **Manual Deploy → Clear build cache & deploy**. The URL is baked in at build time, so saving alone
  changes nothing.

## 4. Check the live site

PowerShell (`curl.exe`, not the `curl` alias). **Passed on 2026-09-27** for https://lifexash-web.onrender.com and
https://lifexash-api.onrender.com.

- [x] `curl.exe https://lifexash-api.onrender.com/api/health` → `{"status":"ok"}`.
- [x] `curl.exe -I https://lifexash-web.onrender.com/sw.js` → `cache-control: no-cache`.
- [x] `curl.exe -I https://lifexash-web.onrender.com/index.html` → `cache-control: no-cache`.
- [x] `curl.exe -I https://lifexash-web.onrender.com/` → `cache-control: no-cache`. (Render's docs don't say
      whether a header on `/index.html` also covers `/`, which is why `render.yaml` sets both.)
      **Result 2026-09-27:** `/` also gets `cache-control: no-cache`.
- [x] Deep link: open `https://lifexash-web.onrender.com/notes/5` in a **new private window** → the app loads
      (login page or "Note not found"), not Render's 404. That proves the SPA rewrite works.
- [x] Register, log in, add a task, write a note and a journal entry, reload → the data is still there (it's in TiDB).
- [x] DevTools → Console: no CORS errors. Network: API calls go to `lifexash-api.onrender.com/api/…`.
- [x] Then run **Round 7** of the [mobile/PWA checklist](mobile-pwa-test-checklist.md) (real phones over HTTPS),
      and Round 6 again on the live site (no API responses in Cache Storage). Passed on **Android** on
      2026-09-28, including the update prompt and Round 6 on the live site. **iPhone: not tested.**

## Everyday use

- **Deploy a change:** push to `main`. The API redeploys when `backend/` changes, and the site when
  `frontend/` changes. New migrations run automatically at start (`alembic upgrade head`).
  Open tabs show "New version available · Reload".
- **Migrations must be backwards compatible.** During a deploy the old version keeps serving until the
  new one is healthy, so both versions briefly use the new schema. Add columns first and remove old ones in
  a later deploy.
- **Roll back:** service → **Events / Deploys** → an earlier deploy → **Rollback**. This rolls back the code,
  **not** the database. A migration that already ran stays. If needed, write a new migration that undoes it.
- **Change a secret:** service → Environment → edit → Save (redeploys). A new `JWT_SECRET` logs everyone out,
  which is the right move if it ever leaks.
- **Backups:** `backup_db.py` is local-only on purpose. Use TiDB Cloud's own backup/export for production data.

## Free plan: what to expect

- **Cold starts:** a free web service spins down after about 15 minutes without traffic. The next request
  wakes it up, which takes around a minute, including `alembic upgrade head`. The site itself (CDN) is always fast.
  Only the first API call waits.
- **TiDB Starter** also scales down when idle. The first query after a long pause can be slow. The connection
  pool is set up for this (`pool_pre_ping`, `pool_recycle=300`, tested in TiDB checklist Round 5).
- **Region:** the API runs in Singapore next to the database. Static sites have no region.

## Troubleshooting

| Symptom | Likely cause → fix |
|---------|--------------------|
| API deploy fails at `alembic upgrade head` with `Access denied` | Wrong user/password in `DATABASE_URL`, or the password isn't URL-encoded |
| API log: `JWT_SECRET … at least 32 characters` or `DATABASE_URL … missing` | Our config check (it refuses to start). Set the variable on lifexash-api |
| Build log: `Python version 3.14.5 is not available` | Change `PYTHON_VERSION` in `render.yaml` to a version Render lists (e.g. its default `3.14.3`) |
| Browser: "blocked by CORS policy" | `CORS_ORIGINS` doesn't exactly match the site URL (https, no trailing `/`, the real suffix) |
| Browser: "Can't reach the server" and no request to onrender.com | `VITE_API_URL` wrong or unset at build time → fix it and **Clear build cache & deploy** |
| `/notes/5` shows Render's 404 on a fresh visit | The rewrite rule is missing. Check lifexash-web → Redirects/Rewrites |
| Old version keeps showing after a deploy | Check the `cache-control` headers in step 4. The update banner appears after one reload |
