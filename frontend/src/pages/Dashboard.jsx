import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { getDashboardSummary, getDashboardWeekly } from "../api/dashboard.js";
import WeeklyChart from "../components/WeeklyChart.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatLongDate, formatTime, todayKey } from "../utils/date.js";
import { getMood } from "../utils/mood.js";

/** "Good morning" before 12:00, "Good afternoon" before 17:00, then "Good evening" — by the browser's clock. */
function greetingFor(now = new Date()) {
  const hour = now.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function StatCard({ title, children }) {
  return (
    <article className="stat-card">
      <h2 className="stat-title">{title}</h2>
      {children}
    </article>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const today = todayKey();

  const [summary, setSummary] = useState(null);
  const [weekly, setWeekly] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    // Promise.all runs both requests at the same time and waits until both have answered.
    Promise.all([getDashboardSummary(today), getDashboardWeekly(today)])
      .then(([summaryData, weeklyData]) => {
        if (cancelled) return;
        setSummary(summaryData);
        setWeekly(weeklyData);
      })
      .catch((err) => !cancelled && setError(getErrorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [today]);

  const greeting = user ? `${greetingFor()}, ${user.name}` : greetingFor();

  if (loading) {
    return (
      <section className="dashboard">
        <h1>{greeting}</h1>
        <p>Loading your dashboard…</p>
      </section>
    );
  }

  if (error || !summary) {
    return (
      <section className="dashboard">
        <h1>{greeting}</h1>
        <p className="form-error" role="alert">{error || "Could not load the dashboard."}</p>
      </section>
    );
  }

  const { tasks_total: total, tasks_completed: done, score, streak_days: streak } = summary;
  const todayMood = summary.today_mood && getMood(summary.today_mood);
  const avgMood = summary.avg_mood_7d;
  const weekIsEmpty = weekly.every((d) => d.tasks_total === 0 && d.mood === null);

  return (
    <section className="dashboard">
      <h1>{greeting}</h1>
      <p className="dashboard-date">{formatLongDate(today)}</p>

      <div className="stat-grid">
        <StatCard title="Today's progress">
          {total === 0 ? (
            <>
              <p className="stat-value">No tasks yet</p>
              <Link to="/planner">Plan your day →</Link>
            </>
          ) : (
            <div className="progress">
              <p className="stat-value">
                {done} of {total} done
              </p>
              <div
                className="progress-track"
                role="progressbar"
                aria-label="Today's tasks done"
                aria-valuenow={score}
                aria-valuemin={0}
                aria-valuemax={100}
              >
                <div className="progress-fill" style={{ width: `${score}%` }} />
              </div>
              <span>{score}%</span>
            </div>
          )}
        </StatCard>

        <StatCard title="Streak">
          {streak > 0 ? (
            <p className="stat-value">
              <span aria-hidden="true">🔥</span> {streak} {streak === 1 ? "day" : "days"}
            </p>
          ) : (
            <p className="stat-value stat-value-small">Start a streak today!</p>
          )}
          <p className="stat-hint">A day counts when at least half of its tasks are done.</p>
        </StatCard>

        <StatCard title="Today's mood">
          {todayMood ? (
            <p className="stat-value">
              <span aria-hidden="true">{todayMood.emoji}</span> {todayMood.label}
            </p>
          ) : (
            <Link to={`/journal/${today}`} className="stat-link">
              Write today's journal →
            </Link>
          )}
        </StatCard>

        <StatCard title="7-day average mood">
          {avgMood === null ? (
            <p className="stat-hint">No journal entries in the last 7 days.</p>
          ) : (
            <p className="stat-value">
              <span aria-hidden="true">{getMood(avgMood).emoji}</span> {avgMood.toFixed(1)}
              <span className="stat-hint"> / 5</span>
            </p>
          )}
        </StatCard>
      </div>

      <div className="dashboard-section">
        <div className="section-header">
          <h2>Next up</h2>
          <Link to="/planner">Open planner →</Link>
        </div>
        {summary.next_tasks.length > 0 ? (
          <ul className="task-list">
            {summary.next_tasks.map((task) => (
              <li key={task.id} className="task-item">
                <span className="task-time">{formatTime(task.task_time)}</span>
                <span className="task-main task-title">{task.title}</span>
                <span className={`badge badge-${task.priority}`}>{task.priority}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-state">
            {total === 0 ? "Nothing planned for today yet." : "All done for today 🎉"}
          </p>
        )}
      </div>

      <div className="dashboard-section">
        <h2>This week</h2>
        {weekIsEmpty ? (
          <div className="empty-state">
            <p>Your week will show up here once you start planning.</p>
            <p>
              <Link to="/planner">Add your first task</Link> or{" "}
              <Link to={`/journal/${today}`}>write today's journal</Link>.
            </p>
          </div>
        ) : (
          <WeeklyChart days={weekly} today={today} />
        )}
      </div>
    </section>
  );
}
