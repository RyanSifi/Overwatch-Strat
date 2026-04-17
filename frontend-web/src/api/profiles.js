import client from "./client";

export const getProfile = () =>
  client.get("/profiles/me/").then((r) => r.data);

export const updateProfile = (data) =>
  client.patch("/profiles/me/", data).then((r) => r.data);

export const syncProfile = () =>
  client.post("/profiles/sync/").then((r) => r.data);

export const login = (username, password) =>
  client.post("/auth/login/", { username, password }).then((r) => r.data);

export const register = (username, email, password) =>
  client.post("/auth/register/", { username, email, password }).then((r) => r.data);
