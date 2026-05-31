/**
 * C-11 相関行列 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. grunfeld.parquet をインポート（録画前）
 *      invest / value / capital / year などの数値列を持つデータ
 *   2. 基本分析 → 相関行列 を開く
 *   3. データ選択 → 数値列を全選択
 *   4. 出力データ名を入力して「作成する」
 *   5. 相関行列テーブルを確認・ハイライト
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c11
 *
 * 出力:
 *   captured/c11/frames/0001.jpg … NNNN.jpg
 *   captured/c11/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  highlightElements,
  humanClick,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c11";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
const OUTPUT_NAME = "grunfeld_corr";

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];

async function navigateToSampleDir(page: AppPage): Promise<void> {
  const fileSelectTab = page.getByRole("tab", {
    name: /ファイル選択|Select File/i,
  });
  if (await fileSelectTab.isVisible()) await fileSelectTab.click();
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
    const dlg = page.getByRole("dialog").or(page.getByRole("alertdialog"));
    await dlg.waitFor({ state: "visible", timeout: 10_000 });
    await dlg.getByRole("button", { name: /^OK$/i }).click();
    await dlg.waitFor({ state: "hidden", timeout: 10_000 });
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
    // ── 録画前準備 ─────────────────────────────────────────────────────────
    await resetWorkspace(page);
    await navigateToSampleDir(page);

    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await fileRow.click();
    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });
    await importDialog.getByRole("textbox").first().fill(TABLE_NAME);
    await importDialog
      .getByRole("button", { name: /^インポート$|^Import$/ })
      .click();
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // ── 録画開始 ──────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: 概要 ───────────────────────────────────────────────────────
    rec.addCue(
      "相関行列で変数間の相関を確認できます",
      "The correlation matrix shows relationships between variables",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 基本分析 → 相関行列 ──────────────────────────────────────
    rec.addCue(
      "「基本分析」→「相関行列」を選択します",
      "Select 'Basic Analysis' → 'Correlation Matrix'",
    );
    const analysisMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /基本分析|Basic Analysis/i });
    await humanClick(page, analysisMenu, 400);
    const corrItem = page.getByRole("menuitem", {
      name: /相関行列|Correlation Matrix/i,
    });
    await corrItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, corrItem, 1000);

    await page
      .getByRole("heading", { name: /相関行列|Correlation Matrix/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: データ選択 ────────────────────────────────────────────────
    rec.addCue(
      `対象データに「${TABLE_NAME}」を選択します`,
      `Select '${TABLE_NAME}' as the target dataset`,
    );
    const dataTrigger = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataTrigger, 400);
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await humanClick(page, tableOption, 800);

    // 列情報ロード待機
    await page
      .getByText(/列情報を読み込んでいます|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});
    await page.waitForTimeout(500);

    // ── step-D: 対象列を全選択 ────────────────────────────────────────────
    rec.addCue("数値列を全選択します", "Select all numeric columns");
    const selectAllBtn = page.getByRole("button", {
      name: /すべて選択|Select All/i,
    });
    await selectAllBtn.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, selectAllBtn, 400);
    await page.waitForTimeout(400);

    // ── step-E: 出力データ名を入力 ────────────────────────────────────────
    rec.addCue("出力データ名を入力します", "Enter the output data name");
    const outputInput = page
      .getByLabel(/出力データ名|Output Data Name/i)
      .first()
      .or(page.getByPlaceholder(/例: correlation_matrix/i));
    await outputInput.fill(OUTPUT_NAME);
    await page.waitForTimeout(400);

    // ── step-F: 作成する ──────────────────────────────────────────────────
    rec.addCue(
      "「作成する」をクリックして相関行列を計算します",
      "Click 'Create' to compute the correlation matrix",
    );
    const runBtn = page.getByRole("button", { name: /作成する|Create/i });
    await humanClick(page, runBtn, 500);

    // 結果テーブルが表示されるまで待機
    const resultTable = page.getByRole("table").first();
    await resultTable.waitFor({ state: "visible", timeout: 30_000 });

    rec.addCue(
      "変数間の相関係数が表示されました",
      "Correlation coefficients between variables are displayed",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultTable], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-11 収録完了");
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
