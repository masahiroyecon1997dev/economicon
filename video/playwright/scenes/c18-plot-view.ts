/**
 * C-18 散布図・ヒストグラムの作成 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. grunfeld.parquet をインポート（録画前）
 *   2. 可視化 → プロットビュー を開く
 *   3. データ選択 → 散布図: X軸=capital、Y軸=invest
 *   4. プロットタイプをヒストグラムに切替 → X軸=invest
 *   5. 各プロット画像をハイライト
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c18
 *
 * 出力:
 *   captured/c18/frames/0001.jpg … NNNN.jpg
 *   captured/c18/meta.json
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

const SCENE_ID = "c18";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";

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
      "散布図やヒストグラムを手軽に作成できます",
      "Create scatter plots and histograms easily",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 可視化 → プロットビュー ──────────────────────────────────
    rec.addCue(
      "「可視化」→「プロットビュー」を選択します",
      "Select 'Visualization' → 'Plot View'",
    );
    const vizMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /^可視化$|^Visualization$/i });
    await humanClick(page, vizMenu, 400);
    const plotViewItem = page.getByRole("menuitem", {
      name: /^プロットビュー$|^Plot View$/i,
    });
    await plotViewItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, plotViewItem, 1000);

    await page
      .getByRole("heading", { name: /プロットビュー|Plot View/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: データ選択 ────────────────────────────────────────────────
    rec.addCue(
      `データに「${TABLE_NAME}」を選択します`,
      `Select '${TABLE_NAME}' as the data source`,
    );
    const dataTrigger = page
      .getByLabel(/^データ$|^Data$/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataTrigger, 400);
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await humanClick(page, tableOption, 800);
    await page.waitForTimeout(500);

    // ── step-D: 散布図 — X軸・Y軸を選択 ─────────────────────────────────
    rec.addCue(
      "散布図のX軸・Y軸を選択します",
      "Select X and Y axes for the scatter plot",
    );

    // プロットタイプ: 散布図（デフォルトのはずだが明示的に選択）
    const scatterBtn = page.getByRole("radio", {
      name: /^散布図$|^Scatter$/i,
    });
    if (await scatterBtn.isVisible()) {
      await humanClick(page, scatterBtn, 300);
    }

    // X軸: capital
    const xTrigger = page
      .getByLabel(/^X軸$|^X.Axis$/i)
      .first()
      .or(page.getByRole("combobox").nth(1));
    await humanClick(page, xTrigger, 400);
    const capitalOpt = page.getByRole("option", { name: "capital", exact: true });
    await capitalOpt.waitFor({ state: "visible" });
    await humanClick(page, capitalOpt, 500);
    await page.waitForTimeout(300);

    // Y軸: invest
    const yTrigger = page
      .getByLabel(/^Y軸$|^Y.Axis$/i)
      .first()
      .or(page.getByRole("combobox").nth(2));
    await humanClick(page, yTrigger, 400);
    const investOpt = page.getByRole("option", { name: "invest", exact: true });
    await investOpt.waitFor({ state: "visible" });
    await humanClick(page, investOpt, 500);

    // プロット生成を待機
    await page
      .getByText(/プロットを生成中|Loading/i)
      .waitFor({ state: "hidden", timeout: 20_000 })
      .catch(() => {});
    await page.waitForTimeout(1500);

    const plotArea = page
      .locator('[data-testid="plot-div"]')
      .or(page.locator(".js-plotly-plot"))
      .or(page.locator("svg").first());
    rec.addCue(
      "capital と invest の散布図が表示されました",
      "Scatter plot of capital vs invest is displayed",
    );
    await highlightElements(page, [plotArea], 2000);

    // ── step-E: ヒストグラムに切替 ────────────────────────────────────────
    rec.addCue(
      "ヒストグラムに切り替えます",
      "Switch to histogram view",
    );
    const histBtn = page.getByRole("radio", {
      name: /^ヒストグラム$|^Histogram$/i,
    });
    await humanClick(page, histBtn, 400);

    // X軸を invest に設定（ヒストグラムは X 軸のみ）
    const histXTrigger = page
      .getByLabel(/^X軸$|^X.Axis$/i)
      .first()
      .or(page.getByRole("combobox").nth(1));
    await humanClick(page, histXTrigger, 400);
    const investHistOpt = page.getByRole("option", { name: "invest", exact: true });
    await investHistOpt.waitFor({ state: "visible" });
    await humanClick(page, investHistOpt, 500);

    await page
      .getByText(/プロットを生成中|Loading/i)
      .waitFor({ state: "hidden", timeout: 20_000 })
      .catch(() => {});
    await page.waitForTimeout(1500);

    rec.addCue(
      "invest のヒストグラムが表示されました",
      "Histogram of invest is displayed",
    );
    await highlightElements(page, [plotArea], 2000);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-18 収録完了");
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
