/**
 * Tauri アプリへの CDP 接続ヘルパー
 *
 * 接続方式は app/e2e/helpers/setupHelpers.ts と同じ CDP パターン。
 * アプリは VS Code タスク「Economicon: App (Debug Port)」で起動しておくこと。
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { Browser, BrowserContext, Page } from "@playwright/test";
import { chromium } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

/**
 * サンプルデータフォルダのパス。
 * 環境変数 ECONOMICON_TEST_SAMPLE_DIR → リポジトリルートの sample/ の順でフォールバック。
 */
export const SAMPLE_DIR =
  process.env.ECONOMICON_TEST_SAMPLE_DIR ??
  path.resolve(__dirname, "../../../sample");

// ---------------------------------------------------------------------------
// 接続
// ---------------------------------------------------------------------------

export interface AppConnection {
  browser: Browser;
  context: BrowserContext;
  page: Page;
}

/**
 * Tauri アプリへ CDP 経由で接続し、操作可能な Page を返す。
 *
 * - 接続先: http://127.0.0.1:9222
 * - devtools:// ページを自動除外（setupHelpers.ts と同ロジック）
 * - viewport を 1920×1080 に固定
 *
 * @throws アプリが起動していない場合にエラーを投げる
 */
export async function connectToApp(): Promise<AppConnection> {
  let browser: Browser;
  try {
    browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  } catch (e) {
    throw new Error(
      "アプリ（ポート9222）が見つかりません。" +
        "VS Code タスク「Economicon: App (Debug Port)」でアプリを起動してから再実行してください。",
      { cause: e },
    );
  }

  const context = browser.contexts()[0];

  // devtools:// ページを除外（setupHelpers.ts と同じロジック）
  const page =
    context.pages().find((p) => !p.url().startsWith("devtools://")) ??
    context.pages()[0];

  if (!page) {
    throw new Error("Tauri アプリのページが見つかりません。");
  }

  await page.setViewportSize({ width: 1920, height: 1080 });

  return { browser, context, page };
}

// ---------------------------------------------------------------------------
// スクリーンショットユーティリティ
// ---------------------------------------------------------------------------

/**
 * captured/{sceneId}/ ディレクトリにスクリーンショットを保存する。
 * ファイル名: step-{step:02d}.png（例: step-01.png）
 */
export async function captureStep(
  page: Page,
  sceneId: string,
  step: number,
): Promise<string> {
  const dir = path.resolve(__dirname, `../captured/${sceneId}`);
  const filePath = path.join(dir, `step-${String(step).padStart(2, "0")}.png`);

  // ディレクトリが存在しない場合は作成
  const { mkdir } = await import("node:fs/promises");
  await mkdir(dir, { recursive: true });

  await page.screenshot({ path: filePath, fullPage: false });
  console.log(`📸 captured: ${filePath}`);
  return filePath;
}
