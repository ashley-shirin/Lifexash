import { useState } from "react";

import { getErrorMessage } from "../api/client.js";
import { createTag } from "../api/tags.js";

/**
 * Pick tags for a note: click existing ones to select/unselect them, or type a name to create one.
 * allTags = every tag of the user, selectedIds = ids picked for this note.
 */
export default function TagPicker({ allTags, selectedIds, onChange, onTagCreated, disabled }) {
  const [newName, setNewName] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const toggle = (id) =>
    onChange(selectedIds.includes(id) ? selectedIds.filter((x) => x !== id) : [...selectedIds, id]);

  const select = (id) => !selectedIds.includes(id) && onChange([...selectedIds, id]);

  const handleAdd = async () => {
    const name = newName.trim();
    setError("");
    if (!name) return;
    if (name.length > 50) {
      setError("Tag name can be at most 50 characters.");
      return;
    }

    // Tag names are case-insensitive: typing "study" when "Study" exists just selects "Study".
    const existing = allTags.find((t) => t.name.toLowerCase() === name.toLowerCase());
    if (existing) {
      select(existing.id);
      setNewName("");
      return;
    }

    setCreating(true);
    try {
      const tag = await createTag(name);
      onTagCreated(tag);
      select(tag.id);
      setNewName("");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  return (
    <fieldset className="tag-picker" disabled={disabled}>
      <legend>
        Tags <span className="optional">(optional)</span>
      </legend>

      {allTags.length > 0 ? (
        <div className="tag-chips">
          {allTags.map((tag) => {
            const selected = selectedIds.includes(tag.id);
            return (
              <button
                key={tag.id}
                type="button"
                className={`chip${selected ? " selected" : ""}`}
                aria-pressed={selected}
                onClick={() => toggle(tag.id)}
              >
                {selected ? "✓ " : ""}
                {tag.name}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="optional">No tags yet — create one below.</p>
      )}

      <div className="tag-add">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          // Enter here adds the tag instead of submitting (saving) the whole note.
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
          placeholder="New tag name"
          aria-label="New tag name"
          maxLength={50}
        />
        <button type="button" className="secondary" onClick={handleAdd} disabled={creating || !newName.trim()}>
          {creating ? "Adding…" : "Add tag"}
        </button>
      </div>
      {error && <span className="field-error">{error}</span>}
    </fieldset>
  );
}
