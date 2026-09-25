import client from "./client.js";

// Thin wrappers around the /notes endpoints; each returns the response data.

// Empty filters are left out, so the URL is just /notes when nothing is selected.
// signal (optional): an AbortController's signal, so the caller can cancel the request.
export const listNotes = ({ q, tagId } = {}, signal) =>
  client
    .get("/notes", { params: { q: q || undefined, tag_id: tagId || undefined }, signal })
    .then((res) => res.data);

export const getNote = (id) => client.get(`/notes/${id}`).then((res) => res.data);

export const createNote = (note) => client.post("/notes", note).then((res) => res.data);

export const updateNote = (id, changes) => client.put(`/notes/${id}`, changes).then((res) => res.data);

export const deleteNote = (id) => client.delete(`/notes/${id}`);

export const togglePin = (id) => client.patch(`/notes/${id}/pin`).then((res) => res.data);
