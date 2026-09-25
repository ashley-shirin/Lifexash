import { Link } from "react-router-dom";

import { timeAgo } from "../utils/time.js";

export default function NoteCard({ note, busy, onTogglePin }) {
  return (
    <li className={`note-card${note.is_pinned ? " pinned" : ""}`}>
      <div className="note-card-head">
        {/* The title link is stretched over the whole card (see .note-link::after in CSS). */}
        <Link to={`/notes/${note.id}`} className="note-link">
          {note.title}
        </Link>
        <button
          type="button"
          className="pin-button"
          onClick={() => onTogglePin(note)}
          disabled={busy}
          aria-pressed={note.is_pinned}
          aria-label={note.is_pinned ? `Unpin "${note.title}"` : `Pin "${note.title}"`}
          title={note.is_pinned ? "Unpin" : "Pin"}
        >
          📌
        </button>
      </div>

      {note.content && <p className="note-preview">{note.content}</p>}

      <div className="note-card-foot">
        {note.tags.map((tag) => (
          <span key={tag.id} className="tag-badge">
            {tag.name}
          </span>
        ))}
        <span className="note-updated">updated {timeAgo(note.updated_at)}</span>
      </div>
    </li>
  );
}
