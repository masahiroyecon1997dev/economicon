import { defineConfig } from "@playwright/test";

/**
 * Playwright E2Eテスト設定
 *
 * ## 実行前提
 * E2Eテストは Tauri サイドカー（Python FastAPI）が起動した状態で実施する。
 * 別ターミナルで `pnpm tauri:dev:debug` を起動（ECONOMICON_DEV_RUN=true）し、
 * アプリが http://localhost:5173 で応答できる状態にしてからテストを実行すること。
 *
 * ## 環境変数
 * - ECONOMICON_TEST_SAMPLE_DIR: サンプルファイルが格納されたディレクトリの絶対パス
 *   例: C:\Users\<username>\Desktop\repos\economicon\sample
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./e2e",
  // E2Eテストはストーリー順に実行するため直列（workerは1）
  fullyParallel: false,
  // CI環境でのみ forbidOnly を有効化
  forbidOnly: !!process.env.CI,
  // リトライ回数（CI環境では1回、ローカルでは0回）
  retries: process.env.CI ? 1 : 0,
  // サイドカー起動を待つため直列実行
  workers: 1,
  // レポート設定
  reporter: "html",

  // アサーションタイムアウト（use の外側・トップレベルに設定する）
  expect: { timeout: 30_000 },

  use: {
    // E2Eは実際の操作タイムアウトを長めに設定（サイドカー応答待機）
    actionTimeout: 30_000,
    // スクリーンショットを失敗時のみ撮影
    screenshot: "only-on-failure",
    // ビデオを失敗時のみ録画
    video: "retain-on-failure",
    // トレースを失敗時のみ保存
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "tauri",
    },
  ],

  // 開発サーバーの自動起動設定
  // Tauri サイドカーが必要なため、通常は事前に `pnpm tauri:dev:debug` を起動しておく。
  // reuseExistingServer: true により、起動済みサーバーがあれば再利用する。
  webServer: {
    command: "pnpm run dev",
    port: 5173,
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
