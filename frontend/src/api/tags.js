import client from "./client.js";

// Thin wrappers around the /tags endpoints; each returns the response data.

export const listTags = () => client.get("/tags").then((res) => res.data);

export const createTag = (name) => client.post("/tags", { name }).then((res) => res.data);

export const deleteTag = (id) => client.delete(`/tags/${id}`);
