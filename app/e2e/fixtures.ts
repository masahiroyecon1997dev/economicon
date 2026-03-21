import { test as base, expect, type Page } from "@playwright/test";
import { spawn } from "child_process";

// 型定義
type tauriFixtures = {
  page: Page;
};

export const test = base.extend<tauriFixtures>({
  page: async ({ playwright }, runTest) => {
    // 1. アプリ起動
    const appProcess = spawn("./src-tauri/target/debug/Economicon.exe", [], {
      shell: true,
      env: {
        ...process.env,
        WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: "--remote-debugging-port=9222",
      },
    });

    // 2. 起動待ち
    await new Promise((resolve) => setTimeout(resolve, 8000));

    // 3. 接続
    const browser = await playwright.chromium.connectOverCDP(
      "http://127.0.0.1:9222",
    );
    const context = browser.contexts()[0];
    const page = context.pages()[0];

    // 4. テストでこれを使えるようにする
    await runTest(page);

    // 5. テスト終了後のクリーンアップ
    await browser.close();
    appProcess.kill();
  },
});

export { expect };
