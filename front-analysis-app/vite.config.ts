import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react-swc";
import path from "node:path";
import license from "rollup-plugin-license";
import { defineConfig } from "vitest/config";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react(), tailwindcss()],

  // Tauri CLI出力を見やすくするための設定
  clearScreen: false,

  server: {
    port: 5173, // Tauriのデフォルトポート
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 5173,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },

  build: {
    rollupOptions: {
      plugins: [
        license({
          thirdParty: {
            // ライセンス情報を出力するファイルパスを指定
            output: path.resolve(__dirname, "dist", "LICENSES.txt"),
            // 開発環境の依存関係も含む場合は true に (通常は本番環境のみで十分)
            includePrivate: false,
            // 複数のバージョンのライブラリが使われている場合にも対応
            multipleVersions: true,
          },
        }),
      ],
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
    include: ["src/components/**/**/*.test.tsx", "src/function/**/*.test.ts"],
  },
});
