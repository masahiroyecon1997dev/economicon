import { defineConfig } from "orval";

export default defineConfig({
  economicon: {
    input: "./openapi.json",
    output: {
      mode: "split",
      target: "./src/api/endpoints.ts",
      schemas: "./src/api/model",
      client: "axios",
      httpClient: "axios",
      override: {
        mutator: {
          path: "./src/api/mutator/custom-instance.ts",
          name: "customInstance",
        },
      },
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
