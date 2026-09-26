import client from "./client.js";

// Thin wrappers around the /dashboard endpoints; each returns the response data.
// Always pass the user's LOCAL today (todayKey()): the backend never guesses "today" itself.

/** dateKey: "YYYY-MM-DD" → { tasks_total, tasks_completed, score, streak_days, today_mood, avg_mood_7d, next_tasks } */
export const getDashboardSummary = (dateKey) =>
  client.get("/dashboard/summary", { params: { date: dateKey } }).then((res) => res.data);

/** endKey: "YYYY-MM-DD" → exactly 7 days (endKey-6 … endKey), oldest first */
export const getDashboardWeekly = (endKey) =>
  client.get("/dashboard/weekly", { params: { end: endKey } }).then((res) => res.data);
