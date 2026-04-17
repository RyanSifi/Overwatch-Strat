import client from "./client";

export const analyzeComposition = (payload) =>
  client.post("/coach/analyze/", payload).then((r) => r.data);
