// "Time ago" helpers for timestamps coming from the backend.
//
// The backend sends timestamps in UTC with a "Z", like "2026-09-25T14:05:00Z". `new Date()` reads
// the "Z" as UTC, so the difference with "now" is correct in any time zone the browser is in.

const UNITS = [
  ["year", 365 * 24 * 60 * 60],
  ["month", 30 * 24 * 60 * 60],
  ["week", 7 * 24 * 60 * 60],
  ["day", 24 * 60 * 60],
  ["hour", 60 * 60],
  ["minute", 60],
];

// Intl.RelativeTimeFormat is built into the browser: it turns (-2, "hour") into "2 hours ago".
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

/** "2026-09-25T14:05:00Z" → "2 hours ago" (or "just now" for under a minute, incl. small clock skew). */
export function timeAgo(isoString, now = new Date()) {
  const seconds = Math.round((now - new Date(isoString)) / 1000);
  if (seconds < 60) return "just now";
  for (const [unit, size] of UNITS) {
    if (seconds >= size) return rtf.format(-Math.floor(seconds / size), unit);
  }
  return "just now";
}
