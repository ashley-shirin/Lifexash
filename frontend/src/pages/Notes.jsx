import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { getErrorMessage } from "../api/client.js";
import { listNotes, togglePin } from "../api/notes.js";
import { deleteTag, listTags } from "../api/tags.js";
import NoteCard from "../components/NoteCard.jsx";

const SEARCH_DELAY_MS = 500;

// Same order as the backend: pinned first, then most recently updated (ties: newest id first).
const byPinnedThenUpdated = (a, b) =>
  b.is_pinned - a.is_pinned || b.updated_at.localeCompare(a.updated_at) || b.id - a.id;

export default function Notes() {
  // Search text and tag filter live in the URL (?q=…&tag=…), so refresh and Back keep them.
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get("q") ?? "";
  const tagParam = searchParams.get("tag") ?? "";
  const tagId = /^\d+$/.test(tagParam) ? Number(tagParam) : null;

  const [searchInput, setSearchInput] = useState(q); // what's in the box right now
  const [notes, setNotes] = useState([]);
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null); // note currently being pinned/unpinned

  const updateParams = (changes) => {
    // Function form: always starts from the latest URL, even when called from an old timer.
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        for (const [key, value] of Object.entries(changes)) {
          if (value) next.set(key, value);
          else next.delete(key);
        }
        return next;
      },
      { replace: true }, // typing shouldn't add one Back-button step per search
    );
  };

  // Debounce: wait until the user stops typing for 500 ms before searching.
  // Every keypress re-runs this effect, and the cleanup cancels the previous timer.
  useEffect(() => {
    if (searchInput.trim() === q) return;
    const timer = setTimeout(() => updateParams({ q: searchInput.trim() }), SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
  }, [searchInput, q]);

  // If the URL's q changes from outside (Back button, a link), show it in the box.
  useEffect(() => {
    setSearchInput((current) => (current.trim() === q ? current : q));
  }, [q]);

  useEffect(() => {
    listTags()
      .then(setTags)
      .catch((err) => setError(getErrorMessage(err)));
  }, []);

  useEffect(() => {
    // AbortController: when q/tag changes, the cleanup below cancels the previous request, so an
    // older search can never overwrite a newer one. signal.aborted also skips the aborted request's
    // own .catch/.finally (axios rejects it with a CanceledError, which isn't a real error).
    const controller = new AbortController();
    const { signal } = controller;
    setLoading(true);
    setError("");
    listNotes({ q, tagId }, signal)
      .then((data) => !signal.aborted && setNotes(data))
      .catch((err) => !signal.aborted && setError(getErrorMessage(err)))
      .finally(() => !signal.aborted && setLoading(false));
    return () => controller.abort();
  }, [q, tagId]);

  const handleTogglePin = async (note) => {
    setBusyId(note.id);
    setError("");
    try {
      const updated = await togglePin(note.id);
      setNotes((prev) => prev.map((n) => (n.id === updated.id ? updated : n)).sort(byPinnedThenUpdated));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  };

  const handleDeleteTag = async (tag) => {
    if (!window.confirm(`Delete the tag "${tag.name}"? Notes with this tag are kept, only the tag is removed.`)) {
      return;
    }
    setError("");
    try {
      await deleteTag(tag.id);
      setTags((prev) => prev.filter((t) => t.id !== tag.id));
      if (tagId === tag.id) {
        updateParams({ tag: null }); // the filter pointed at the deleted tag; the list re-fetches
      } else {
        setNotes((prev) => prev.map((n) => ({ ...n, tags: n.tags.filter((t) => t.id !== tag.id) })));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const isFiltering = Boolean(q) || tagId !== null;

  return (
    <section className="notes-page">
      <div className="planner-header">
        <h1>Notes</h1>
        <Link to="/notes/new" className="button">
          + New note
        </Link>
      </div>

      <input
        type="search"
        className="note-search"
        placeholder="Search title or content…"
        aria-label="Search notes"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        maxLength={200}
      />

      {tags.length > 0 && (
        <div className="tag-chips" role="group" aria-label="Filter by tag">
          <button
            type="button"
            className={`chip${tagId === null ? " selected" : ""}`}
            aria-pressed={tagId === null}
            onClick={() => updateParams({ tag: null })}
          >
            All
          </button>
          {tags.map((tag) => (
            <span key={tag.id} className={`chip${tagId === tag.id ? " selected" : ""}`}>
              <button
                type="button"
                className="chip-label"
                aria-pressed={tagId === tag.id}
                onClick={() => updateParams({ tag: tagId === tag.id ? null : String(tag.id) })}
              >
                {tag.name}
              </button>
              <button
                type="button"
                className="chip-remove"
                aria-label={`Delete tag "${tag.name}"`}
                title="Delete tag"
                onClick={() => handleDeleteTag(tag)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {error && <p className="form-error" role="alert">{error}</p>}

      {loading ? (
        <p>Loading notes…</p>
      ) : notes.length === 0 ? (
        <p className="empty-state">
          {isFiltering ? "No notes match your search." : "No notes yet. Write your first one!"}
        </p>
      ) : (
        <ul className="note-list">
          {notes.map((note) => (
            <NoteCard key={note.id} note={note} busy={busyId === note.id} onTogglePin={handleTogglePin} />
          ))}
        </ul>
      )}
    </section>
  );
}
