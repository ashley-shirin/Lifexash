import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { createNote, deleteNote, getNote, updateNote } from "../api/notes.js";
import { listTags } from "../api/tags.js";
import TagPicker from "../components/TagPicker.jsx";

const EMPTY_FORM = { title: "", content: "", is_pinned: false, tag_ids: [] };

function validate({ title }) {
  const errors = {};
  if (!title.trim()) errors.title = "Title is required.";
  else if (title.trim().length > 200) errors.title = "Title can be at most 200 characters.";
  return errors;
}

/** Used for both /notes/new (no noteId) and /notes/:noteId. */
export default function NoteEditor() {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const isNew = noteId === undefined;
  const validId = isNew || /^\d+$/.test(noteId);

  const [form, setForm] = useState(EMPTY_FORM);
  const [allTags, setAllTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!validId) return;
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setLoadError("");

    Promise.all([listTags(), isNew ? null : getNote(noteId)])
      .then(([tags, note]) => {
        if (cancelled) return;
        setAllTags(tags);
        setForm(
          note
            ? { title: note.title, content: note.content, is_pinned: note.is_pinned, tag_ids: note.tags.map((t) => t.id) }
            : EMPTY_FORM,
        );
      })
      .catch((err) => {
        if (cancelled) return;
        // 404 = doesn't exist OR belongs to another user; the backend doesn't tell us which, on purpose.
        if (err.response?.status === 404) setNotFound(true);
        else setLoadError(getErrorMessage(err));
      })
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [noteId, isNew, validId]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const found = validate(form);
    setErrors(found);
    setServerError("");
    if (Object.keys(found).length > 0) return;

    const payload = { ...form, title: form.title.trim() };
    setSaving(true);
    try {
      if (isNew) await createNote(payload);
      else await updateNote(noteId, payload);
      navigate("/notes");
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${form.title || "this note"}"? This cannot be undone.`)) return;
    setSaving(true);
    setServerError("");
    try {
      await deleteNote(noteId);
      navigate("/notes");
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSaving(false);
    }
  };

  if (!validId || notFound) {
    return (
      <section>
        <h1>Note not found</h1>
        <p>This note doesn't exist or may have been deleted.</p>
        <Link to="/notes">← Back to notes</Link>
      </section>
    );
  }

  if (loading) return <p>Loading…</p>;

  if (loadError) {
    return (
      <section>
        <p className="form-error" role="alert">{loadError}</p>
        <Link to="/notes">← Back to notes</Link>
      </section>
    );
  }

  return (
    <section className="note-editor">
      <Link to="/notes">← Back to notes</Link>
      <h1>{isNew ? "New note" : "Edit note"}</h1>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <label>
          Title
          <input name="title" value={form.title} onChange={handleChange} maxLength={200} autoFocus={isNew} />
          {errors.title && <span className="field-error">{errors.title}</span>}
        </label>

        <label>
          Content
          <textarea name="content" rows={12} value={form.content} onChange={handleChange} />
        </label>

        <TagPicker
          allTags={allTags}
          selectedIds={form.tag_ids}
          onChange={(tag_ids) => setForm((prev) => ({ ...prev, tag_ids }))}
          onTagCreated={(tag) =>
            setAllTags((prev) => [...prev, tag].sort((a, b) => a.name.localeCompare(b.name)))
          }
          disabled={saving}
        />

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.is_pinned}
            onChange={(e) => setForm({ ...form, is_pinned: e.target.checked })}
          />
          📌 Pin this note to the top
        </label>

        <div className="modal-actions">
          {!isNew && (
            <button type="button" className="danger-button" onClick={handleDelete} disabled={saving}>
              Delete
            </button>
          )}
          <Link to="/notes" className="button secondary">
            Cancel
          </Link>
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : isNew ? "Create note" : "Save changes"}
          </button>
        </div>
      </form>
    </section>
  );
}
