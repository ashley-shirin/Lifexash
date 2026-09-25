import { useEffect, useRef, useState } from "react";

import { getErrorMessage } from "../api/client.js";
import { createTask, updateTask } from "../api/tasks.js";
import { nextFullHour } from "../utils/date.js";

const PRIORITIES = ["low", "medium", "high"];

function validate({ title, task_date, task_time }) {
  const errors = {};
  if (!title.trim()) errors.title = "Title is required.";
  else if (title.trim().length > 200) errors.title = "Title can be at most 200 characters.";
  if (!task_date) errors.task_date = "Date is required.";
  if (!task_time) errors.task_time = "Time is required.";
  return errors;
}

/**
 * Add/edit modal. Mount it only while it should be open.
 * task = the task being edited, or null to add a new one on `defaultDate`.
 */
export default function TaskForm({ task, defaultDate, onClose, onSaved }) {
  const dialogRef = useRef(null);
  const isEdit = Boolean(task);

  const [form, setForm] = useState(() => ({
    title: task?.title ?? "",
    description: task?.description ?? "",
    task_date: task?.task_date ?? defaultDate,
    task_time: task ? task.task_time.slice(0, 5) : nextFullHour(), // "HH:MM:SS" → "HH:MM"
    priority: task?.priority ?? "medium",
  }));
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [saving, setSaving] = useState(false);

  // showModal() opens <dialog> as a real modal: dims the page, traps focus, and Esc closes it.
  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => dialog.close();
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const found = validate(form);
    setErrors(found);
    setServerError("");
    if (Object.keys(found).length > 0) return;

    const payload = { ...form, title: form.title.trim(), description: form.description.trim() || null };
    setSaving(true);
    try {
      const saved = isEdit ? await updateTask(task.id, payload) : await createTask(payload);
      onSaved(saved);
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSaving(false);
    }
  };

  return (
    // onCancel fires when the user presses Esc; we close through the parent so state stays in sync.
    <dialog
      ref={dialogRef}
      className="modal"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <h2>{isEdit ? "Edit task" : "Add task"}</h2>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <label>
          Title
          <input name="title" value={form.title} onChange={handleChange} maxLength={200} autoFocus />
          {errors.title && <span className="field-error">{errors.title}</span>}
        </label>

        <label>
          Description <span className="optional">(optional)</span>
          <textarea name="description" rows={3} value={form.description} onChange={handleChange} />
        </label>

        <div className="form-row">
          <label>
            Date
            <input name="task_date" type="date" value={form.task_date} onChange={handleChange} />
            {errors.task_date && <span className="field-error">{errors.task_date}</span>}
          </label>
          <label>
            Time
            <input name="task_time" type="time" value={form.task_time} onChange={handleChange} />
            {errors.task_time && <span className="field-error">{errors.task_time}</span>}
          </label>
          <label>
            Priority
            <select name="priority" value={form.priority} onChange={handleChange}>
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p[0].toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="modal-actions">
          <button type="button" className="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Add task"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
