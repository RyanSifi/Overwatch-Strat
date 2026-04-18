import client from "./client";

export const getHeroes = (params = {}) =>
  client.get("/heroes/", { params }).then((r) => r.data);

export const getHero = (slug) =>
  client.get(`/heroes/${slug}/`).then((r) => r.data);

export const getHeroCounters = (slug) =>
  client.get(`/heroes/${slug}/counters/`).then((r) => r.data);

export const suggestCounters = (enemyHeroes) =>
  client.post("/counters/suggest/", { enemy_heroes: enemyHeroes }).then((r) => r.data);

export const getHeroSynergies = (slug) =>
  client.get(`/heroes/${slug}/synergies/`).then((r) => r.data);

export const getMetaComps = (params = {}) =>
  client.get("/meta/", { params }).then((r) => r.data);

export const getLatestPatch = () => client.get("/patches/latest/").then((r) => r.data);
