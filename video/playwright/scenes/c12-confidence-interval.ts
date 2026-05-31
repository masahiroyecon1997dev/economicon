/**
 * C-12 信頼区間の計算 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. grunfeld.parquet をインポート（録画前）
 *   2. 基本分析 → 信頼区間 を開く
 *   3. データ選択 → 列選択（invest）→ 統計量タイプ（平均, t分布）
 *   4. 信頼水準 95% を選択して「計算する」
 *   5. 結果を確認・ハイライト
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c12
 *
 * 出力:
 *   captured/c12/frames/0001.jpg … NNNN.jpg
 *   captured/c12/meta.json
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

const SCENE_ID = "c12";
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
      "母平均・比率などの信頼区間を計算できます",
      "You can compute confidence intervals for means, proportions, and more",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 基本分析 → 信頼区間 ──────────────────────────────────────
    rec.addCue(
      "「基本分析」→「信頼区間」を選択します",
      "Select 'Basic Analysis' → 'Confidence Interval'",
    );
    const analysisMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /基本分析|Basic Analysis/i });
    await humanClick(page, analysisMenu, 400);
    const ciItem = page.getByRole("menuitem", {
      name: /信頼区間|Confidence Interval/i,
    });
    await ciItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, ciItem, 1000);

    await page
      .getByRole("heading", { name: /信頼区間|Confidence Interval/i })
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

    // ── step-D: 対象列を選択 ──────────────────────────────────────────────
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
    await page.waitForTimeout(400);

    // ── step-E: 統計量タイプを選択（平均 / t分布）────────────────────────
    rec.addCue(
      "統計量タイプ「平均（t分布）」を選択します",
      "Select 'Mean (t-distribution)' as the statistic type",
    );
    const statTypeTrigger = page
      .getByLabel(/統計量タイプ|Statistic Type/i)
      .first()
      .or(page.getByRole("combobox").nth(2));
    await humanClick(page, statTypeTrigger, 400);
    const meanOption = page.getByRole("option", {
      name: /平均（t分布）|Mean.*t|t.*distribution/i,
    });
    await meanOption.waitFor({ state: "visible" });
    await humanClick(page, meanOption, 600);
    await page.waitForTimeout(400);

    // ── step-F: 信頼水準 95% を選択 ──────────────────────────────────────
    rec.addCue("信頼水準 95% を選択します", "Select 95% confidence level");
    // 「主要な水準から選択」モード（デフォルト）で 95% ボタンをクリック
    const cl95Btn = page
      .getByRole("radio", { name: /95%/i })
      .or(page.getByRole("button", { name: /95%/i }))
      .first();
    if (await cl95Btn.isVisible()) {
      await humanClick(page, cl95Btn, 400);
    }
    await page.waitForTimeout(400);

    // ── step-G: 計算する ──────────────────────────────────────────────────
    rec.addCue(
      "「計算する」をクリックして信頼区間を算出します",
      "Click 'Calculate' to compute the confidence interval",
    );
    const runBtn = page.getByRole("button", {
      name: /^計算する$|^Calculate$/i,
    });
    await humanClick(page, runBtn, 500);

    // 結果が表示されるまで待機
    const resultContainer = page
      .getByRole("table")
      .or(page.getByText(/信頼区間|Confidence Interval/i).last());
    await resultContainer.waitFor({ state: "visible", timeout: 30_000 });

    rec.addCue(
      "95% 信頼区間が表示されました",
      "The 95% confidence interval is displayed",
    );
    await page.waitForTimeout(2000);
    const resultEl = page.getByRole("table").first();
    await highlightElements(page, [resultEl], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-12 収録完了");
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
