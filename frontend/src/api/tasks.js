import client from "./client.js";

// Thin wrappers around the /tasks endpoints; each returns the response data.

export const listTasksForDay = (dateKey) =>
  client.get("/tasks", { params: { date: dateKey } }).then((res) => res.data);

export const listTasksInRange = (start, end) =>
  client.get("/tasks", { params: { start, end } }).then((res) => res.data);

export const createTask = (task) => client.post("/tasks", task).then((res) => res.data);

export const updateTask = (id, changes) => client.put(`/tasks/${id}`, changes).then((res) => res.data);

export const deleteTask = (id) => client.delete(`/tasks/${id}`);

export const toggleTask = (id) => client.patch(`/tasks/${id}/toggle`).then((res) => res.data);
