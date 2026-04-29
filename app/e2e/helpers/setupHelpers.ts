import type { PlaywrightWorkerArgs } from "@playwright/test";

export async function setupTauriApp(
  playwrightInstance: PlaywrightWorkerArgs["playwright"],
) {
  // アプリが起動してポートが開くまで少し待つ
  await new Promise((resolve) => setTimeout(resolve, 5000));

  let browser;
  try {
    browser = await playwrightInstance.chromium.connectOverCDP(
      "http://127.0.0.1:9222",
    );
  } catch (e) {
    throw new Error(
      "アプリ（ポート9222）が見つかりません。手動で引数付き起動しているか確認してください。",
      { cause: e },
    );
  }
  const context = browser.contexts()[0];
  const page = context.pages()[0];

  return page;
}
