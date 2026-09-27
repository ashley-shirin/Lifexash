import { formatTime } from "../utils/date.js";

export default function TaskItem({ task, busy, onToggle, onEdit, onDelete }) {
  return (
    <li className={`task-item${task.is_completed ? " done" : ""}`}>
      {/* The label around the checkbox gives it a bigger tap area (44 × 44 px) on phones. */}
      <label className="task-check">
        <input
          type="checkbox"
          checked={task.is_completed}
          onChange={() => onToggle(task)}
          disabled={busy}
          aria-label={`Mark "${task.title}" as ${task.is_completed ? "not done" : "done"}`}
        />
      </label>
      <div className="task-main">
        <span className="task-title">{task.title}</span>
        {task.description && <span className="task-desc">{task.description}</span>}
      </div>
      <span className="task-time">{formatTime(task.task_time)}</span>
      <span className={`badge badge-${task.priority}`}>{task.priority}</span>
      <div className="task-actions">
        <button type="button" className="link-button" onClick={() => onEdit(task)} disabled={busy}>
          Edit
        </button>
        <button type="button" className="link-button danger" onClick={() => onDelete(task)} disabled={busy}>
          Delete
        </button>
      </div>
    </li>
  );
}
