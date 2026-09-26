import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { listJournalMonth } from "../api/journal.js";
import { addMonths, formatLongDate, formatMonth, monthKeyOf, parseMonthKey, toDateKey, todayKey } from "../utils/date.js";
import { getMood } from "../utils/mood.js";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** All the cells of a month grid: null for the empty cells before the 1st, then "YYYY-MM-DD" per day. */
function buildMonthCells(monthKey) {
  const first = parseMonthKey(monthKey);
  const daysInMonth = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate(); // day 0 = last day of the month before
  const leadingBlanks = (first.getDay() + 6) % 7; // getDay() is 0 for Sunday; our weeks start on Monday
  const days = Array.from({ length: daysInMonth }, (_, i) =>
    toDateKey(new Date(first.getFullYear(), first.getMonth(), i + 1)),
  );
  return [...Array(leadingBlanks).fill(null), ...days];
}

export default function Journal() {
  // The shown month lives in the URL (?month=YYYY-MM), so a refresh keeps you on the same month.
  const [searchParams, setSearchParams] = useSearchParams();
  const today = todayKey();
  const currentMonth = monthKeyOf(today);
  const urlMonth = searchParams.get("month");
  const month = parseMonthKey(urlMonth) ? urlMonth : currentMonth;

  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    // "cancelled" ignores a slow response for a month you've already clicked away from.
    let cancelled = false;
    setLoading(true);
    setError("");
    listJournalMonth(month)
      .then((data) => !cancelled && setEntries(data))
      .catch((err) => !cancelled && setError(getErrorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [month]);

  const goTo = (monthKey) => setSearchParams({ month: monthKey });

  const entryByDate = Object.fromEntries(entries.map((e) => [e.entry_date, e]));
  const average = entries.length ? entries.reduce((sum, e) => sum + e.mood, 0) / entries.length : null;

  return (
    <section className="journal">
      <h1>Journal</h1>

      <div className="day-nav">
        <button type="button" className="secondary" onClick={() => goTo(addMonths(month, -1))}>
          ← Prev
        </button>
        <button type="button" className="secondary" onClick={() => goTo(currentMonth)} disabled={month === currentMonth}>
          This month
        </button>
        {/* Later months only contain future days, which can't be written yet. */}
        <button
          type="button"
          className="secondary"
          onClick={() => goTo(addMonths(month, 1))}
          disabled={month >= currentMonth}
        >
          Next →
        </button>
      </div>

      <h2 className="day-title">{formatMonth(month)}</h2>

      {error && <p className="form-error" role="alert">{error}</p>}

      {loading ? (
        <p>Loading entries…</p>
      ) : (
        <>
          <div className="calendar">
            {WEEKDAYS.map((day) => (
              <div key={day} className="calendar-weekday">
                {day}
              </div>
            ))}

            {buildMonthCells(month).map((dateKey, i) => {
              if (!dateKey) return <div key={`blank-${i}`} aria-hidden="true" />;

              const entry = entryByDate[dateKey];
              const mood = entry && getMood(entry.mood);
              const dayNumber = Number(dateKey.slice(8));
              const classes = ["calendar-day", entry && "has-entry", dateKey === today && "today"]
                .filter(Boolean)
                .join(" ");
              const label = `${formatLongDate(dateKey)}${mood ? ` — ${mood.label}` : ""}`;

              // "YYYY-MM-DD" strings compare correctly as text, so > means "later day".
              if (dateKey > today) {
                return (
                  <div key={dateKey} className={`${classes} future`} aria-disabled="true" title="Future day">
                    <span className="calendar-number">{dayNumber}</span>
                  </div>
                );
              }

              return (
                <Link key={dateKey} to={`/journal/${dateKey}`} className={classes} aria-label={label} title={label}>
                  <span className="calendar-number">{dayNumber}</span>
                  {mood && <span className="calendar-mood">{mood.emoji}</span>}
                </Link>
              );
            })}
          </div>

          <p className="journal-average">
            {average === null
              ? "No entries this month yet."
              : `Average mood this month: ${getMood(average).emoji} ${average.toFixed(1)} (${entries.length} ${
                  entries.length === 1 ? "entry" : "entries"
                })`}
          </p>
        </>
      )}
    </section>
  );
}
