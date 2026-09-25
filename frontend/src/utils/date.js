// Date helpers that always work in the user's LOCAL time zone.
//
// Never use date.toISOString().slice(0, 10): it converts to UTC first, so in India (UTC+5:30)
// it returns yesterday's date between 00:00 and 05:30 local time.
// And never use new Date("2026-09-25"): a bare YYYY-MM-DD string is parsed as UTC midnight.

const pad = (n) => String(n).padStart(2, "0");

/** Date object → "YYYY-MM-DD" for its local calendar day. */
export function toDateKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** "YYYY-MM-DD" → Date at local midnight, or null if the string isn't a real date. */
export function parseDateKey(key) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(key ?? "");
  if (!match) return null;
  const [, y, m, d] = match.map(Number);
  const date = new Date(y, m - 1, d);
  // Rejects things like 2026-02-31, which JavaScript would silently roll over to March.
  return toDateKey(date) === key ? date : null;
}

export const todayKey = () => toDateKey(new Date());

/** Shift a "YYYY-MM-DD" by some days (negative goes back). Month/year ends are handled. */
export function addDays(key, days) {
  const date = parseDateKey(key);
  date.setDate(date.getDate() + days);
  return toDateKey(date);
}

/** Next full hour as "HH:00" (e.g. 14:20 → "15:00"). After 23:00 it stays "23:59" so it's still today. */
export function nextFullHour(now = new Date()) {
  const hour = now.getHours() + 1;
  return hour > 23 ? "23:59" : `${pad(hour)}:00`;
}

/** "YYYY-MM-DD" → "Friday, 25 September 2026" */
export function formatLongDate(key) {
  return parseDateKey(key).toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** "18:30:00" → "6:30 PM" */
export function formatTime(time) {
  const [h, m] = time.split(":").map(Number);
  const suffix = h < 12 ? "AM" : "PM";
  return `${h % 12 || 12}:${pad(m)} ${suffix}`;
}
