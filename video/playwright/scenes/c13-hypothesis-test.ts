/**
 * C-13 仮説検定 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. grunfeld.parquet をインポート（録画前）
 *   2. 基本分析 → 仮説検定 を開く
 *   3. 検定タイプ: t 検定（1標本）を選択
 *   4. データ・列（invest）を選択
 *   5. 「検定を実行」をクリック
 *   6. p 値・結果を確認・ハイライト
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c13
 *
 * 出力:
 *   captured/c13/frames/0001.jpg … NNNN.jpg
 *   captured/c13/meta.json
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

const SCENE_ID = "c13";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
const TARGET_COL = "invest";

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
      "t 検定・z 検定・F 検定などの仮説検定を実行できます",
      "You can run t-tests, z-tests, F-tests, and more",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 基本分析 → 仮説検定 ──────────────────────────────────────
    rec.addCue(
      "「基本分析」→「仮説検定」を選択します",
      "Select 'Basic Analysis' → 'Hypothesis Test'",
    );
    const analysisMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /基本分析|Basic Analysis/i });
    await humanClick(page, analysisMenu, 400);
    const htItem = page.getByRole("menuitem", {
      name: /仮説検定|Hypothesis Test/i,
    });
    await htItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, htItem, 1000);

    await page
      .getByRole("heading", { name: /仮説検定|Hypothesis Test/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: 検定タイプを選択（t 検定）────────────────────────────────
    rec.addCue(
      "検定タイプ「t 検定」を選択します",
      "Select 't-test' as the test type",
    );
    const testTypeTrigger = page
      .getByLabel(/検定タイプ|Test Type/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, testTypeTrigger, 400);
    const tTestOption = page.getByRole("option", {
      name: /^t[ _]検定|^t.test|one.sample.t/i,
    });
    await tTestOption.waitFor({ state: "visible" });
    await humanClick(page, tTestOption, 600);
    await page.waitForTimeout(500);

    // ── step-D: データ選択 ────────────────────────────────────────────────
    rec.addCue(
      `対象データに「${TABLE_NAME}」を選択します`,
      `Select '${TABLE_NAME}' as the target dataset`,
    );
    // サンプル 1 のデータセレクト（最初の combobox）
    const dataCombobox = page
      .getByLabel(/^対象データ|^Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataCombobox, 400);
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

    // ── step-E: 対象列を選択 ──────────────────────────────────────────────
    rec.addCue(
      `対象列に「${TARGET_COL}」を選択します`,
      `Select '${TARGET_COL}' as the target column`,
    );
    const colTrigger = page
      .getByLabel(/対象列|Target Column/i)
      .first()
      .or(page.getByRole("combobox").nth(1));
    await humanClick(page, colTrigger, 400);
    const colOption = page.getByRole("option", {
      name: TARGET_COL,
      exact: true,
    });
    await colOption.waitFor({ state: "visible" });
    await humanClick(page, colOption, 600);
    await page.waitForTimeout(500);

    // ── step-F: 検定を実行 ────────────────────────────────────────────────
    rec.addCue(
      "「検定を実行」をクリックします",
      "Click 'Run Test' to execute the hypothesis test",
    );
    const runBtn = page.getByRole("button", {
      name: /^検定を実行$|^Run Test$/i,
    });
    await humanClick(page, runBtn, 500);

    // 結果が表示されるまで待機
    const pValueText = page.getByText(/p[ ._]?値|p[ ._]?value/i).first();
    await pValueText.waitFor({ state: "visible", timeout: 30_000 });

    rec.addCue(
      "t 統計量と p 値が表示されました",
      "The t-statistic and p-value are displayed",
    );
    await page.waitForTimeout(2000);

    const resultEl = page
      .getByRole("table")
      .first()
      .or(pValueText.locator("..").locator(".."));
    await highlightElements(page, [resultEl], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-13 収録完了");
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
