import client from "./client";

export const getMaps = (params = {}) =>
  client.get("/maps/", { params }).then((r) => r.data);

export const getMapGuide = (slug) =>
  client.get(`/maps/${slug}/guide/`).then((r) => r.data);
