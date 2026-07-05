/**
 * C-01 CSV ファイルのインポート — Playwright 動画収録スクリプト
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c01
 *
 * 出力:
 *   captured/c01/frames/0001.jpg … NNNN.jpg
 *   captured/c01/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  highlightElements,
  humanClick,
  maskDirUsername,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c01";
const FILE_NAME = "回帰分析サンプル多変量.csv";

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];

async function navigateToSampleDir(page: AppPage): Promise<void> {
  const fileSelectTab = page.getByRole("tab", {
    name: /ファイル選択|Select File/i,
  });
  if (await fileSelectTab.isVisible()) {
    await fileSelectTab.click();
  }

  const sep = path.sep;
  const segments = SAMPLE_DIR.split(sep).filter((s) => s.length > 0);

  for (const segment of segments) {
    const folderRow = page
      .getByRole("row", { name: segment })
      .filter({ hasNot: page.locator('[data-file="true"]') });

    if (await folderRow.isVisible()) {
      await folderRow.click();
      await page.waitForTimeout(300);
    }
  }
}

async function resetWorkspace(page: AppPage): Promise<void> {
  const resetButton = page.getByTestId("left-menu-reset-workspace");
  await resetButton.waitFor({ state: "visible", timeout: 90_000 });

  if (await resetButton.isEnabled()) {
    await resetButton.click();
    const confirmDialog = page
      .getByRole("dialog")
      .or(page.getByRole("alertdialog"));
    await confirmDialog.waitFor({ state: "visible", timeout: 10_000 });
    await confirmDialog.getByRole("button", { name: /^OK$/i }).click();
    await confirmDialog.waitFor({ state: "hidden", timeout: 10_000 });
  }

  await page
    .getByRole("heading", { name: /ファイルをインポート|Select File/i })
    .waitFor({ state: "visible", timeout: 30_000 });
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // ── 録画前準備 ────────────────────────────────────────────────────────
    await resetWorkspace(page);
    await navigateToSampleDir(page);
    await page.waitForTimeout(500);
    await maskDirUsername(page);

    // ── 録画開始 ────────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: インポート画面の説明 ─────────────────────────────────────
    rec.addCue(
      "インポート画面でファイルを選択します",
      "Select a file on the import screen",
    );
    await page.waitForTimeout(1500);

    // ── step-B: CSV ファイルをクリック ────────────────────────────────────
    rec.addCue(`${FILE_NAME} をクリックします`, `Click on ${FILE_NAME}`);
    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await humanClick(page, fileRow, 800);

    // ── step-C: インポートダイアログ ─────────────────────────────────────
    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });

    rec.addCue(
      "エンコーディングやテーブル名を確認します",
      "Check encoding and table name",
    );
    await page.waitForTimeout(1500);

    // ── インポート実行 ────────────────────────────────────────────────────
    rec.addCue(
      "「インポート」をクリックして取り込みます",
      "Click 'Import' to load the file",
    );
    const importBtn = importDialog.getByRole("button", {
      name: /^インポート$|^Import$/,
    });
    await humanClick(page, importBtn, 2000);
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // ── step-D: 結果テーブルを確認 ───────────────────────────────────────
    const tableEl = page.getByRole("table").first();
    await tableEl.waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      "CSV データがテーブルとして取り込まれました",
      "The CSV data is now loaded as a table",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [tableEl], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-01 収録完了");
    console.log(`   フレーム数: ${info.totalFrames}`);
    console.log(`   長さ: ${(info.durationMs / 1000).toFixed(1)}s`);
    console.log(`   出力先: video/playwright/captured/${SCENE_ID}/`);
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ 収録失敗:", err);
  process.exit(1);
});
