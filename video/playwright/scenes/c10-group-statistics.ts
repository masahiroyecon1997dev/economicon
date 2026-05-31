/**
 * C-10 グループ別統計量 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. ユニオン1.csv をインポート（録画前）
 *      ※ category（グループキー）× amount（集計列）
 *   2. 基本分析 → グループ別統計量 を開く
 *   3. Step1: 対象データを選択して「Step 2 に進む」
 *   4. Step2: category をグループキーに、amount を集計列に割り当て
 *   5. 統計量（平均・標準偏差）を選択して「作成する」
 *   6. 結果テーブルを確認
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c10
 *
 * 出力:
 *   captured/c10/frames/0001.jpg … NNNN.jpg
 *   captured/c10/meta.json
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

const SCENE_ID = "c10";
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1";
const GROUP_COL = "category";
const STAT_COL = "amount";
const OUTPUT_NAME = "union1_group_stats";

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

    const fileRow = page.getByRole("row", { name: CSV_FILE_NAME });
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
      "グループ別に統計量を計算できます",
      "You can calculate statistics per group",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 基本分析 → グループ別統計量 ──────────────────────────────
    rec.addCue(
      "「基本分析」→「グループ別統計量」を選択します",
      "Select 'Basic Analysis' → 'Group Statistics'",
    );
    const analysisMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /基本分析|Basic Analysis/i });
    await humanClick(page, analysisMenu, 400);
    const groupStatsItem = page.getByRole("menuitem", {
      name: /グループ別統計量|Group Statistics/i,
    });
    await groupStatsItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, groupStatsItem, 1000);

    await page
      .getByRole("heading", { name: /グループ別統計量|Group Statistics/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: Step1 — データ選択 ────────────────────────────────────────
    rec.addCue(
      "Step 1: 対象データを選択します",
      "Step 1: Select the target dataset",
    );
    const dataTrigger = page.getByRole("combobox").first();
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

    // 「Step 2 に進む」をクリック
    rec.addCue("「Step 2 に進む」をクリックします", "Click 'Go to Step 2'");
    const nextStepBtn = page.getByRole("button", {
      name: /Step 2 に進む|Next Step/i,
    });
    await humanClick(page, nextStepBtn, 800);

    await page
      .getByRole("heading", { name: /Step 2/i })
      .waitFor({ state: "visible", timeout: 10_000 })
      .catch(() => {});
    await page.waitForTimeout(500);

    // ── step-D: Step2 — 列の役割割り当て ─────────────────────────────────
    rec.addCue(
      `「${GROUP_COL}」列をグループキーに割り当てます`,
      `Assign '${GROUP_COL}' column as the group key`,
    );

    // category 列をグループキーに設定
    const groupKeyBtn = page
      .getByRole("row", { name: new RegExp(GROUP_COL) })
      .getByRole("button", { name: /グループキー|Group Key/i })
      .first()
      .or(
        page.getByRole("button", { name: /グループキー|Group Key/i }).first(),
      );
    if (await groupKeyBtn.isVisible()) {
      await humanClick(page, groupKeyBtn, 400);
    }

    await page.waitForTimeout(400);

    // amount 列を集計列に設定
    rec.addCue(
      `「${STAT_COL}」列を集計列に割り当てます`,
      `Assign '${STAT_COL}' column as the stat column`,
    );
    const statColBtn = page
      .getByRole("row", { name: new RegExp(STAT_COL) })
      .getByRole("button", { name: /集計列|Stat|Aggregate/i })
      .first()
      .or(page.getByRole("button", { name: /集計列|Aggregate/i }).first());
    if (await statColBtn.isVisible()) {
      await humanClick(page, statColBtn, 400);
    }
    await page.waitForTimeout(400);

    // 統計量を全選択
    rec.addCue(
      "統計量を選択します（平均・標準偏差など）",
      "Select statistics (mean, std dev, etc.)",
    );
    const selectAllBtn = page.getByRole("button", {
      name: /すべて選択|Select All/i,
    });
    if (await selectAllBtn.isVisible()) {
      await humanClick(page, selectAllBtn, 400);
    } else {
      // 個別に選択
      const meanCb = page.getByRole("checkbox", { name: /^平均$|^Mean$/i });
      const stdCb = page.getByRole("checkbox", { name: /標準偏差|Std Dev/i });
      if ((await meanCb.isVisible()) && !(await meanCb.isChecked()))
        await meanCb.click();
      if ((await stdCb.isVisible()) && !(await stdCb.isChecked()))
        await stdCb.click();
    }
    await page.waitForTimeout(400);

    // 出力データ名を入力
    const outputInput = page.getByLabel(/出力データ名|Output Data Name/i);
    if (await outputInput.isVisible()) {
      const currentVal = await outputInput.inputValue();
      if (!currentVal) await outputInput.fill(OUTPUT_NAME);
    }

    // ── step-E: 作成する ──────────────────────────────────────────────────
    rec.addCue(
      "「作成する」をクリックして集計を実行します",
      "Click 'Create' to run the group aggregation",
    );
    const runBtn = page.getByRole("button", { name: /作成する|Create/i });
    await humanClick(page, runBtn, 500);

    // 結果確認
    const resultTable = page.getByRole("table").first();
    await resultTable.waitFor({ state: "visible", timeout: 30_000 });

    rec.addCue(
      "グループ別の統計量が計算されました",
      "Group statistics have been calculated",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultTable], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-10 収録完了");
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
