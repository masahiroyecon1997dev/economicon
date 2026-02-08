import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2Eテスト設定
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: "./e2e",
  // 並列実行の設定
  fullyParallel: true,
  // CI環境でのみfailOnConsoleErrorを有効化
  forbidOnly: !!process.env.CI,
  // リトライ回数（CI環境では2回、ローカルでは0回）
  retries: process.env.CI ? 2 : 0,
  // 並列ワーカー数（CI環境では1、ローカルではCPUコア数の半分）
  workers: process.env.CI ? 1 : undefined,
  // レポート設定
  reporter: "html",

  use: {
    // ベースURL ポート: 1420 (Tauri Default)
    baseURL: "http://localhost:1420",
    // スクリーンショットを失敗時のみ撮影
    screenshot: "only-on-failure",
    // ビデオを失敗時のみ録画
    video: "retain-on-failure",
    // トレースを失敗時のみ保存
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],

  // 開発サーバーの自動起動設定
  webServer: {
    command: "pnpm run dev",
    // ベースURL ポート: 1420 (Tauri Default)
    port: 1420,
    reuseExistingServer: !process.env.CI,
  },
});
