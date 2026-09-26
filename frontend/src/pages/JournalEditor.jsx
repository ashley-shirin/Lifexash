import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { createJournal, deleteJournal, getJournalByDate, updateJournal } from "../api/journal.js";
import { formatLongDate, monthKeyOf, parseDateKey, todayKey } from "../utils/date.js";
import { MOODS } from "../utils/mood.js";

const EMPTY_FORM = { mood: null, title: "", content: "" };

function validate({ mood, title, content }) {
  const errors = {};
  if (mood === null) errors.mood = "Pick a mood.";
  if (title.trim().length > 200) errors.title = "Title can be at most 200 characters.";
  if (!content.trim()) errors.content = "Write something about your day.";
  return errors;
}

/** /journal/:dateKey — edits that day's entry if it exists, otherwise shows an empty form for that day. */
export default function JournalEditor() {
  const { dateKey } = useParams();
  const navigate = useNavigate();
  const validDate = parseDateKey(dateKey) !== null;
  const isFuture = validDate && dateKey > todayKey();
  const backTo = validDate ? `/journal?month=${monthKeyOf(dateKey)}` : "/journal";

  const [entry, setEntry] = useState(null); // the saved entry, or null if the day has none yet
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!validDate || isFuture) return;
    let cancelled = false;
    setLoading(true);
    setLoadError("");

    getJournalByDate(dateKey)
      .then((data) => {
        if (cancelled) return;
        setEntry(data);
        setForm({ mood: data.mood, title: data.title ?? "", content: data.content });
      })
      .catch((err) => {
        if (cancelled) return;
        // 404 = no entry for this day yet → show an empty form to write one.
        if (err.response?.status === 404) {
          setEntry(null);
          setForm(EMPTY_FORM);
        } else {
          setLoadError(getErrorMessage(err));
        }
      })
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [dateKey, validDate, isFuture]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const found = validate(form);
    setErrors(found);
    setServerError("");
    if (Object.keys(found).length > 0) return;

    // A blank title is sent as null: "no title".
    const payload = { mood: form.mood, title: form.title.trim() || null, content: form.content };
    setSaving(true);
    try {
      if (entry) await updateJournal(entry.id, payload);
      else await createJournal({ ...payload, entry_date: dateKey });
      navigate(backTo);
    } catch (err) {
      const message = getErrorMessage(err);
      // 409: the entry was created meanwhile (e.g. in another tab).
      setServerError(err.response?.status === 409 ? `${message}. Reload the page to edit it.` : message);
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete your journal entry for ${formatLongDate(dateKey)}? This cannot be undone.`)) return;
    setSaving(true);
    setServerError("");
    try {
      await deleteJournal(entry.id);
      navigate(backTo);
    } catch (err) {
      setServerError(getErrorMessage(err));
      setSaving(false);
    }
  };

  if (!validDate) {
    return (
      <section>
        <h1>Invalid date</h1>
        <p>This page needs a real date, like /journal/{todayKey()}.</p>
        <Link to="/journal">← Back to journal</Link>
      </section>
    );
  }

  if (isFuture) {
    return (
      <section>
        <h1>{formatLongDate(dateKey)}</h1>
        <p>This day hasn't happened yet — you can write about it when it comes.</p>
        <Link to={backTo}>← Back to journal</Link>
      </section>
    );
  }

  if (loading) return <p>Loading…</p>;

  if (loadError) {
    return (
      <section>
        <p className="form-error" role="alert">{loadError}</p>
        <Link to={backTo}>← Back to journal</Link>
      </section>
    );
  }

  return (
    <section className="journal-editor">
      <Link to={backTo}>← Back to journal</Link>
      <h1>{formatLongDate(dateKey)}</h1>
      <p className="optional">{entry ? "Edit your entry for this day." : "No entry for this day yet."}</p>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <fieldset className="mood-picker">
          <legend>How was your day?</legend>
          <div className="mood-options">
            {MOODS.map((mood) => (
              <button
                key={mood.value}
                type="button"
                className={`mood-option${form.mood === mood.value ? " selected" : ""}`}
                aria-pressed={form.mood === mood.value}
                onClick={() => setForm({ ...form, mood: mood.value })}
                disabled={saving}
              >
                <span className="mood-emoji" aria-hidden="true">{mood.emoji}</span>
                {mood.label}
              </button>
            ))}
          </div>
          {errors.mood && <span className="field-error">{errors.mood}</span>}
        </fieldset>

        <label>
          <span>
            Title <span className="optional">(optional)</span>
          </span>
          <input name="title" value={form.title} onChange={handleChange} maxLength={200} />
          {errors.title && <span className="field-error">{errors.title}</span>}
        </label>

        <label>
          What happened today?
          <textarea name="content" rows={12} value={form.content} onChange={handleChange} />
          {errors.content && <span className="field-error">{errors.content}</span>}
        </label>

        <div className="modal-actions">
          {entry && (
            <button type="button" className="danger-button" onClick={handleDelete} disabled={saving}>
              Delete
            </button>
          )}
          <Link to={backTo} className="button secondary">
            Cancel
          </Link>
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </section>
  );
}
