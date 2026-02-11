import { defineConfig } from "orval";

export default defineConfig({
  economicon: {
    input: "./openapi.json",
    output: {
      mode: "split",
      target: "./src/api/endpoints.ts",
      schemas: "./src/api/model",
      client: "fetch",
      httpClient: "fetch",
    },
  },
  economiconZod: {
    input: "./openapi.json",
    output: {
      mode: "tags-split",
      target: "./src/api/zod",
      client: "zod",
    },
  },
});
