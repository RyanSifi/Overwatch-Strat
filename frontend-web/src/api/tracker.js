import client from "./client";

export const getSessions = (params = {}) =>
  client.get("/tracker/sessions/", { params }).then((r) => r.data);

export const createSession = (data) =>
  client.post("/tracker/sessions/", data).then((r) => r.data);

export const deleteSession = (id) =>
  client.delete(`/tracker/sessions/${id}/`).then((r) => r.data);

export const getStats = () =>
  client.get("/tracker/stats/").then((r) => r.data);
