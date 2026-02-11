import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  input: "http://localhost:8000/openapi.json",
  output: "src/api/generated",
  plugins: [
    "@hey-api/typescript",
    "zod",
    // クライアントは生成するが、実際の通信を差し替える準備をする
    "@hey-api/client-fetch",
  ],
});
