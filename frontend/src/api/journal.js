import client from "./client.js";

// Thin wrappers around the /journal endpoints; each returns the response data.

/** monthKey: "YYYY-MM" */
export const listJournalMonth = (monthKey) =>
  client.get("/journal", { params: { month: monthKey } }).then((res) => res.data);

/** dateKey: "YYYY-MM-DD". Rejects with a 404 if that day has no entry yet. */
export const getJournalByDate = (dateKey) => client.get(`/journal/date/${dateKey}`).then((res) => res.data);

export const createJournal = (entry) => client.post("/journal", entry).then((res) => res.data);

export const updateJournal = (id, changes) => client.put(`/journal/${id}`, changes).then((res) => res.data);

export const deleteJournal = (id) => client.delete(`/journal/${id}`);
