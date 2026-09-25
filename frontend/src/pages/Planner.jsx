import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { deleteTask, listTasksForDay, toggleTask } from "../api/tasks.js";
import TaskForm from "../components/TaskForm.jsx";
import TaskItem from "../components/TaskItem.jsx";
import { addDays, formatLongDate, parseDateKey, todayKey } from "../utils/date.js";

export default function Planner() {
  // The selected day lives in the URL (?date=YYYY-MM-DD), so a refresh keeps you on the same day.
  const [searchParams, setSearchParams] = useSearchParams();
  const today = todayKey();
  const urlDate = searchParams.get("date");
  const selectedDate = parseDateKey(urlDate) ? urlDate : today;

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null); // task currently being toggled/deleted
  const [reloadKey, setReloadKey] = useState(0); // bump to re-fetch the day
  // null = modal closed, { task: null } = adding, { task } = editing
  const [formState, setFormState] = useState(null);

  useEffect(() => {
    // "cancelled" ignores a slow response for a day you've already clicked away from.
    let cancelled = false;
    setLoading(true);
    setError("");
    listTasksForDay(selectedDate)
      .then((data) => !cancelled && setTasks(data))
      .catch((err) => !cancelled && setError(getErrorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [selectedDate, reloadKey]);

  const goTo = (dateKey) => setSearchParams({ date: dateKey });

  const handleToggle = async (task) => {
    setBusyId(task.id);
    setError("");
    try {
      const updated = await toggleTask(task.id);
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (task) => {
    if (!window.confirm(`Delete "${task.title}"? This cannot be undone.`)) return;
    setBusyId(task.id);
    setError("");
    try {
      await deleteTask(task.id);
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleSaved = () => {
    setFormState(null);
    // Re-fetch instead of patching the list: keeps the time order and handles a task moved to another day.
    setReloadKey((k) => k + 1);
  };

  const doneCount = tasks.filter((t) => t.is_completed).length;
  const percent = tasks.length ? Math.round((doneCount / tasks.length) * 100) : 0;

  return (
    <section className="planner">
      <div className="planner-header">
        <h1>Planner</h1>
        <button type="button" onClick={() => setFormState({ task: null })}>
          + Add task
        </button>
      </div>

      <div className="day-nav">
        <button type="button" className="secondary" onClick={() => goTo(addDays(selectedDate, -1))}>
          ← Prev
        </button>
        <button type="button" className="secondary" onClick={() => goTo(today)} disabled={selectedDate === today}>
          Today
        </button>
        <button type="button" className="secondary" onClick={() => goTo(addDays(selectedDate, 1))}>
          Next →
        </button>
        <input
          type="date"
          aria-label="Pick a day"
          value={selectedDate}
          onChange={(e) => e.target.value && goTo(e.target.value)}
        />
      </div>

      <h2 className="day-title">
        {formatLongDate(selectedDate)}
        {selectedDate === today && <span className="today-tag">Today</span>}
      </h2>

      {error && <p className="form-error" role="alert">{error}</p>}

      {loading ? (
        <p>Loading tasks…</p>
      ) : tasks.length === 0 ? (
        <p className="empty-state">No tasks for this day. Add one!</p>
      ) : (
        <>
          <div className="progress">
            <span>
              {doneCount} of {tasks.length} done ({percent}%)
            </span>
            <div
              className="progress-track"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div className="progress-fill" style={{ width: `${percent}%` }} />
            </div>
          </div>

          <ul className="task-list">
            {tasks.map((task) => (
              <TaskItem
                key={task.id}
                task={task}
                busy={busyId === task.id}
                onToggle={handleToggle}
                onEdit={(t) => setFormState({ task: t })}
                onDelete={handleDelete}
              />
            ))}
          </ul>
        </>
      )}

      {formState && (
        <TaskForm
          task={formState.task}
          defaultDate={selectedDate}
          onClose={() => setFormState(null)}
          onSaved={handleSaved}
        />
      )}
    </section>
  );
}
