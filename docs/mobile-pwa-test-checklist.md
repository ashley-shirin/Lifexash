# Mobile layout + PWA: manual test checklist

Status: Rounds 1–6 passed on 2026-09-27. Round 7 passed on Android (Chrome) on 2026-09-28 against
https://lifexash-web.onrender.com, including the update prompt and Round 6 on the live site. iPhone was not
tested. The "waking up" notice was seen live after 20 minutes idle. The local 8000 ms check is still open.

Covers the `feature/mobile-pwa` changes: phone layout (bottom nav, 44 px touch targets, full-screen task
modal, compact journal calendar), the web app manifest and icons, the service worker (app shell only),
the offline banner and the "New version available" prompt.

Rounds 1–6 run on your PC. Round 7 is marked **after deploy**: a real phone can only install the app and
run the service worker over **HTTPS** (browsers allow service workers only on HTTPS or `localhost`), so
it needs the deployed site.

## Setup

- [x] Backend running (`uvicorn app.main:app --reload`) with some data (`python -m scripts.seed_demo you@example.com --yes`).
- [x] Round 1 uses the dev server: `npm run dev` → <http://localhost:5173>.
- [x] Rounds 2–6 need the **production build**, because the service worker is not active in `npm run dev`:
  1. In `backend/.env`, set `CORS_ORIGINS=http://localhost:5173,http://localhost:4173` (the preview
     server runs on port 4173), then restart the backend.
  2. From `frontend/`: `npm run build`, then `npm run preview` → <http://localhost:4173>.
- [x] Use an Incognito window for Rounds 2–6, so no service worker or cache is left over from an
      earlier run. Closing the window deletes them.

## Round 1: Phone-size layout (375 px)

DevTools (F12) → device toolbar (Ctrl+Shift+M) → **iPhone SE (375 × 667)**, and also try **Galaxy S20
Ultra / 412 px**. On every page:
- no sideways scrolling: swipe left and right, and the bottom scrollbar must not appear
- text is readable without zooming
- nothing is hidden behind the bottom bar: scroll to the very end of the page

Chrome shows how big each element is when you hover it in the Elements panel. Use it to check the
**44 px** touch targets.

**Navigation**
- [x] Logged out (`/login`): the top bar shows LifeXash · Log in · Register. There's **no** bottom bar.
- [x] Logged in: the top bar shows only "LifeXash". The **bottom bar** shows 5 items (Dashboard, Planner, Notes,
      Journal, Profile), each with an icon and a label, all on one line.
- [x] The current page is highlighted in indigo. It stays highlighted on sub-pages: `/notes/5` → Notes, `/journal/2026-09-01` → Journal.
- [x] Each bottom-bar item is at least 44 px tall (it's 56 px).
- [x] Widen the window above 640 px → the bottom bar disappears and the links are back in the top bar.

**Login / Register**
- [x] The card fits the width. Inputs and the button are at least 44 px tall.
- [x] A validation error (empty form → Log in) wraps nicely and doesn't widen the page.

**Dashboard**
- [x] The stat cards are in one column, and the weekly chart fits without sideways scrolling.

**Planner**
- [x] ← Prev · Today · Next → share one row, and the date picker has its own full-width row.
- [x] Task row: the checkbox and title are on top, with time · priority · Edit · Delete underneath. A very long title
      with no spaces wraps and doesn't overflow.
- [x] Tapping the area **around** the checkbox (not just the box) toggles the task.
- [x] **Add task** → the modal fills the **whole screen**, with no rounded corners and no page visible
      behind it. All fields and Cancel / Save are reachable (scroll if needed). Esc / Cancel still close it.
- [x] Edit a task → the same full-screen modal, with the values filled in.

**Notes list**
- [x] The search box has full width, and the notes are in one column.
- [x] Tag chips wrap onto several lines, and each chip is 44 px tall. The × (delete tag) is easy to hit and
      doesn't trigger the filter by mistake.
- [x] The 📌 pin button toggles the pin. Tapping the rest of the card opens the note.

**Note editor**
- [x] "← Back to notes" is easy to tap (44 px high).
- [x] Title, content, tag picker ("Add" row) and the Pinned checkbox fit the width.
- [x] Delete · Cancel · Save fit in one row, or wrap without overflowing.
- [x] Tapping a text field does **not** zoom the page in, on an iPhone preset (16 px font).

**Journal calendar**
- [x] Still **7 columns** (Mon–Sun), with no sideways scrolling.
- [x] Every day with an entry shows its **mood emoji** in full: not cut off, and not overlapping the day number.
- [x] Today has the indigo border and its emoji is still fully visible.
- [x] ← Prev · This month · Next → fit in one row.

**Journal editor**
- [x] All 5 mood buttons are in one row, and the emoji and label (Awful … Great) are readable.
- [x] The long date heading (e.g. "Wednesday, 24 September 2026") wraps without overflowing.

**Profile**
- [x] A long email address wraps instead of widening the page. The Log out button is at least 44 px tall.

## Round 2: Manifest and installability

On <http://localhost:4173>. (Lighthouse removed its "PWA" category in Chrome 126, so installability
is checked in DevTools.)

- [x] DevTools → **Application → Manifest**:
  - name **LifeXash**
  - short name **LifeXash**
  - start URL `/dashboard`
  - display `standalone`
  - theme colour `#4f46e5`
  - background `#f9fafb`
- [x] The **Installability** section shows no errors.
- [x] Icons: 192 px, 512 px and a 512 px **maskable** icon load. Tick "Show only the minimum safe area for
      maskable icons" → "LX" is fully inside the circle.
- [x] The browser tab shows the LX favicon.
- [x] `/apple-touch-icon.png` opens (180 × 180, indigo square with "LX").
- [x] **Application → Service workers:** `sw.js` is **activated and is running**.
- [x] Optional: Lighthouse (Mobile) → Accessibility and Best practices have no new red items.

## Round 3: Install on desktop Chrome

Installing needs a normal window, not Incognito.

- [x] The address bar shows the **Install** icon (monitor with an arrow). Click it → Install.
- [x] The app opens in its **own window**, with no address bar, at **/dashboard**, and the title bar is indigo.
- [x] The Start menu / desktop shortcut uses the LX icon.
- [x] Log out and log in inside the app window. It works like the browser version.
- [x] Uninstall: app window → ⋮ → Uninstall LifeXash.

## Round 4: Offline banner

- [x] DevTools → **Network → throttling: Offline** → the amber banner appears straight away:
      "You're offline. Changes can't be saved right now."
- [x] While offline, try to add a task → the modal shows the same offline message as an error. Nothing is saved.
- [x] While offline, **reload** the page → the app still loads (the app shell comes from the service
      worker) and the banner is shown. Data can't load, so you see an error or empty state. That's
      expected, because the API is never cached.
- [x] Switch back to **No throttling** → the banner disappears without a reload. Adding a task works again.

## Round 5: Update prompt

- [x] With the preview tab open, make a visible change (e.g. change the Dashboard heading text), then
      `npm run build`. Restart `npm run preview`.
- [x] Reload the tab once → the blue banner appears: **"New version available · Reload"**. The page
      still shows the **old** text (nothing is replaced silently).
- [x] Click **Reload** → the page reloads with the new text, and the banner is gone.
- [x] DevTools → Application → Service workers shows only one active worker (no "waiting" one left).
- [x] Undo the test change and rebuild.

(If the banner doesn't appear: in Application → Service workers, "Update on reload" must be **off**.)

## Round 6: No API data in Cache Storage

- [x] Log in and open every page: Dashboard, Planner (add and toggle a task), Notes (open a note), Journal
      (open an entry), Profile.
- [x] DevTools → **Application → Cache Storage** → there is only one cache, `workbox-precache-v2-…`. It contains
      only `index.html`, `assets/*.js`, `assets/*.css`, the icons and `manifest.webmanifest`. There is **no**
      URL with `:8000` or `/api`.
- [x] Double-check in the Console (paste and press Enter):
  ```js
  const urls = [];
  for (const name of await caches.keys()) {
    for (const req of await (await caches.open(name)).keys()) urls.push(req.url);
  }
  console.log(urls.length, "cached:", urls);
  console.log("API responses cached:", urls.filter((u) => u.includes("/api")).length); // must be 0
  ```
- [x] DevTools → **Network**, reload → the API requests (`/api/...`) show a normal size, **not**
      "(ServiceWorker)" or "(disk cache)" in the Size column.
- [x] Shared-device check: log out → Cache Storage still contains only the app shell. No notes, tasks or
      journal text are left on the device.

## Round 7: After deploy (needs HTTPS). Android passed 2026-09-28, iPhone not tested

**Android (Chrome)**
- [x] Open the site → ⋮ → **Install app** (or the install banner) → the icon on the home screen is the LX icon,
      shaped by the phone's mask (circle or squircle) with nothing cut off.
- [x] Opening it from the home screen → full screen, no address bar, starts on the dashboard, and the status
      bar is indigo. (Starts on the dashboard: confirmed 2026-09-28.)

**iPhone (Safari): not tested**
- [ ] Share → **Add to Home Screen** → the LX (apple-touch-icon) appears. It opens without Safari's address bar.
- [ ] The bottom bar sits above the home-indicator line (safe area), and nothing is hidden behind it.
- [ ] Tapping inputs doesn't zoom the page in.

**Both phones** (only Android was tested)
- [x] Repeat the Round 1 checks with a real finger: every button is easy to hit, and the calendar emojis are visible.
      Android: the bottom bar works, the task form is full screen, tapping inputs doesn't zoom, and the journal
      calendar emojis are fully visible.
- [x] Airplane mode → the offline banner appears. Turn it off → the banner goes away.
- [x] Deploy a small change → open the installed app → "New version available · Reload" appears, and
      Reload shows the change. Android 2026-09-28, with the "waking up" notice deploy: the banner appeared,
      and Reload loaded the new version and removed the banner.
- [ ] **"Waking up the server" notice, locally** (PC, `npm run dev`). DevTools → Network → throttling
      dropdown → **Add…** → a custom profile with **Latency 8000 ms**, then select it. ("Slow 3G" adds only
      about 2 s, which is under the 5 s limit.) Then:
  - Reload the dashboard → after about 5 s a small blue notice appears at the bottom: "Waking up the
    server… the first request after a quiet period can take up to a minute". It disappears as soon as the
    data arrives. Nothing is retried: Network shows each request only once.
  - The same on `/login`: log in → the notice appears after 5 s and disappears when you're logged in (or
    when the error shows).
  - At 375 px (device toolbar) the notice sits **above** the bottom bar and doesn't cover it. You can still
    tap the bottom bar and buttons while it's shown.
  - Back to **No throttling** → normal use never shows it (requests take well under 5 s).
  - Known limit: while the full-screen task form is open, the notice is hidden behind it (a modal
    `<dialog>` is drawn above everything else). Saving still works.
- [x] **"Waking up the server" notice, live** (after deploy): leave the site unused for 20+ minutes (the free
      API sleeps after about 15), then open the installed app → the notice appears while the API wakes up
      and goes away when the dashboard loads.
      **2026-09-28 (Android):** the API answered at normal speed, so it wasn't asleep, and the notice correctly
      didn't appear. **Later on 2026-09-28:** after 20 minutes idle, the notice appeared while the API woke up.
- [x] Round 6 again on the live site (desktop Chrome DevTools against the deployed URL). No API responses
      are in Cache Storage. 2026-09-28: only the Workbox precache (app shell), with no `/api` responses.

**Hosting settings to check while deploying**
- [x] `sw.js` is served with `Cache-Control: no-cache` (otherwise updates can be delayed by the HTTP cache).
- [x] Unknown paths (e.g. `/notes/5`) are rewritten to `index.html` (SPA fallback), so a first visit to a deep
      link works before the service worker is installed.
- [x] The backend's `CORS_ORIGINS` contains the deployed frontend URL (no CORS errors on the live site).
