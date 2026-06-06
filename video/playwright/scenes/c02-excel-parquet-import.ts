/**
 * C-02 Excel / Parquet のインポート — Playwright 動画収録スクリプト
 *
 * 1 録画で Excel → Parquet の 2 種類のインポートを連続して収録する。
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c02
 *
 * 出力:
 *   captured/c02/frames/0001.jpg … NNNN.jpg
 *   captured/c02/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  humanClick,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c02";
const EXCEL_FILE_NAME = "Excelデータ.xlsx";
const PARQUET_FILE_NAME = "grunfeld.parquet";

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

/** ヘッダーメニュー経由でインポート画面に戻る */
async function goToImportScreen(page: AppPage): Promise<void> {
  const fileMenuBtn = page.getByRole("banner").getByRole("button", {
    name: /ファイル|File/i,
  });
  await humanClick(page, fileMenuBtn, 400);

  const importMenuItem = page.getByRole("menuitem", {
    name: /^取り込み$|^Import$/i,
  });
  await importMenuItem.waitFor({ state: "visible", timeout: 5_000 });
  await humanClick(page, importMenuItem, 800);

  await page
    .getByRole("heading", { name: /ファイルをインポート|Select File/i })
    .waitFor({ state: "visible", timeout: 15_000 });
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

    // ── 録画開始 ────────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ====================================================================
    // ── PART 1: Excel インポート ──────────────────────────────────────────
    // ====================================================================

    rec.addCue(
      "まず Excel ファイルをインポートします",
      "First, let's import an Excel file",
    );
    await page.waitForTimeout(1500);

    // Excel ファイルをクリック
    rec.addCue(
      `${EXCEL_FILE_NAME} をクリックします`,
      `Click on ${EXCEL_FILE_NAME}`,
    );
    const excelRow = page.getByRole("row", { name: EXCEL_FILE_NAME });
    await excelRow.waitFor({ state: "visible", timeout: 15_000 });
    await humanClick(page, excelRow, 800);

    // インポートダイアログ
    const dialog1 = page.getByRole("dialog");
    await dialog1.waitFor({ state: "visible", timeout: 10_000 });

    rec.addCue(
      "設定を確認して「インポート」をクリックします",
      "Check settings and click 'Import'",
    );
    await page.waitForTimeout(1200);

    const importBtn1 = dialog1.getByRole("button", {
      name: /^インポート$|^Import$/,
    });
    await humanClick(page, importBtn1, 2000);
    await dialog1.waitFor({ state: "hidden", timeout: 30_000 });

    // 結果確認
    await page
      .getByRole("table")
      .first()
      .waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      "Excel データが取り込まれました",
      "Excel data has been imported",
    );
    await page.waitForTimeout(2000);

    // ====================================================================
    // ── PART 2: Parquet インポート ─────────────────────────────────────────
    // ====================================================================

    rec.addCue(
      "続いて Parquet 形式のファイルをインポートします",
      "Now let's import a Parquet file",
    );
    await goToImportScreen(page);
    await navigateToSampleDir(page);
    await page.waitForTimeout(500);

    // Parquet ファイルをクリック
    rec.addCue(
      `${PARQUET_FILE_NAME} をクリックします`,
      `Click on ${PARQUET_FILE_NAME}`,
    );
    const parquetRow = page.getByRole("row", { name: PARQUET_FILE_NAME });
    await parquetRow.waitFor({ state: "visible", timeout: 15_000 });
    await humanClick(page, parquetRow, 800);

    // インポートダイアログ
    const dialog2 = page.getByRole("dialog");
    await dialog2.waitFor({ state: "visible", timeout: 10_000 });

    rec.addCue(
      "Parquet は設定が少なくシンプルにインポートできます",
      "Parquet import has fewer settings — it's straightforward",
    );
    await page.waitForTimeout(1200);

    const importBtn2 = dialog2.getByRole("button", {
      name: /^インポート$|^Import$/,
    });
    await humanClick(page, importBtn2, 2000);
    await dialog2.waitFor({ state: "hidden", timeout: 30_000 });

    // 結果確認
    await page
      .getByRole("table")
      .first()
      .waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      "Parquet データも取り込まれました",
      "Parquet data has been imported as well",
    );
    await page.waitForTimeout(2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-02 収録完了");
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
