/**
 * C-09 基本統計量 — Playwright 動画収録スクリプト
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c09
 *
 * 出力:
 *   captured/c09/frames/0001.jpg … NNNN.jpg
 *   captured/c09/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  highlightElements,
  humanCheck,
  humanClick,
  maskDirUsername,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c09";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
/** 結果テーブルで強調表示する列（初期チェック済みのため外さない） */
const COLUMNS = ["invest", "value", "capital"];
/** 初期チェックを外す列（動画では invest/value/capital のみ残す） */
const UNCHECK_COLUMNS = ["firm", "year"];
/** 初期チェックを外す統計量パターン（動画では 平均/標準偏差 のみ残す） */
const UNCHECK_STAT_PATTERNS: RegExp[] = [
  /^有効サンプル数$|^N$|^Count$/i,
  /^中央値$|^Median$/i,
  /^最小値$|^Min(imum)?$/i,
  /^最大値$|^Max(imum)?$/i,
];

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

/**
 * ファイルブラウザで SAMPLE_DIR まで降りていく。
 * app/e2e/helpers/appHelpers.ts の navigateFileBrowserToDir と同ロジック。
 */
async function navigateToSampleDir(
  page: Awaited<ReturnType<typeof connectToApp>>["page"],
): Promise<void> {
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

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // ── ① ワークスペースをリセット ──────────────────────────────────────
    const resetButton = page.getByTestId("left-menu-reset-workspace");
    await resetButton.waitFor({ state: "visible", timeout: 90_000 });
    await maskDirUsername(page);

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

    // ── ② SAMPLE_DIR へ移動して grunfeld.parquet をインポート ────────────
    await navigateToSampleDir(page);

    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await humanClick(page, fileRow);

    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });

    const importBtn = importDialog.getByRole("button", {
      name: /^インポート$|^Import$/,
    });
    await humanClick(page, importBtn, 2000);
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // DataPreview に遷移してテーブルタブが表示されるまで待機
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // ── ③ 録画開始 ────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: データプレビュー ──────────────────────────────────────────
    rec.addCue(
      "Grunfeld データが取り込まれました",
      "Grunfeld data has been imported",
    );
    await page.waitForTimeout(1500);

    // ── ④ 「基本分析」メニューを開く ─────────────────────────────────────
    rec.addCue(
      "「基本分析」→「基本統計量」を選択します",
      "Select 'Basic Analysis' → 'Descriptive Statistics'",
    );

    const menuBtn = page.getByRole("banner").getByRole("button", {
      name: /基本分析|Basic Analysis/i,
    });
    await humanClick(page, menuBtn, 500);

    const basicStatsItem = page.getByRole("menuitem", {
      name: /基本統計量|Descriptive Statistics/i,
    });
    await basicStatsItem.waitFor({ state: "visible", timeout: 5_000 });
    await page.waitForTimeout(400);

    // ── ⑤ 「基本統計量」をクリック ──────────────────────────────────────
    await humanClick(page, basicStatsItem, 1000);

    await page
      .getByRole("heading", { name: /基本統計量|Descriptive Statistics/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-B: テーブルを選択 ────────────────────────────────────────────
    rec.addCue("集計するテーブルを選択します", "Select the table to analyze");

    const dataSelect = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataSelect, 400);

    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, tableOption, 800);

    // 列リストのロード完了を待機
    await page
      .getByText(/列情報を読み込んでいます|Loading column info/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // ── step-C: 不要な列のチェックを外す ────────────────────────────────
    rec.addCue(
      "invest・value・capital の列だけを選択します（firm・year のチェックを外します）",
      "Keep only invest, value, and capital — uncheck firm and year",
    );

    for (const col of UNCHECK_COLUMNS) {
      const checkbox = page.getByRole("checkbox", { name: col });
      if (await checkbox.isVisible()) {
        await humanCheck(page, checkbox, false, 350);
      }
    }
    await page.waitForTimeout(500);

    // ── step-D: 不要な統計量のチェックを外す ────────────────────────────
    rec.addCue(
      "平均と標準偏差だけを残し、他の統計量のチェックを外します",
      "Keep only mean and std dev — uncheck the other statistics",
    );

    for (const pattern of UNCHECK_STAT_PATTERNS) {
      const checkbox = page.getByRole("checkbox", { name: pattern });
      if (await checkbox.isVisible()) {
        await humanCheck(page, checkbox, false, 350);
      }
    }
    await page.waitForTimeout(500);

    // ── ⑥ 「計算する」をクリック ────────────────────────────────────────
    rec.addCue(
      "「計算する」をクリックして実行します",
      "Click 'Calculate' to run",
    );

    const calcBtn = page.getByRole("button", {
      name: /^(計算する|Calculate)$/i,
    });
    await humanClick(page, calcBtn, 500);

    // 結果テーブルが表示されるまで待機
    await page
      .getByRole("table")
      .waitFor({ state: "visible", timeout: 30_000 });

    // ── step-E: 結果概要 ────────────────────────────────────────────────
    rec.addCue(
      "基本統計量の計算結果が表示されました",
      "Descriptive statistics results are displayed",
    );
    await page.waitForTimeout(2000);

    // ── step-F: 選択した列を強調 ─────────────────────────────────────────
    rec.addCue(
      "選択した invest・value・capital の列が結果に表示されています",
      "The selected columns invest, value, and capital appear in the results",
    );
    const resultTable = page.getByRole("table");
    const colLocators = COLUMNS.map((col) =>
      resultTable
        .locator("th, td")
        .filter({ hasText: new RegExp(`^${col}$`) })
        .first(),
    );
    await highlightElements(page, colLocators, 3000);

    // ── step-G: 選択した統計量行を強調 ───────────────────────────────────
    rec.addCue(
      "平均と標準偏差の行が選択した統計量に対応しています",
      "The mean and std dev rows correspond to the selected statistics",
    );
    const statLocators = [
      resultTable
        .locator("th, td")
        .filter({ hasText: /^(平均|Mean)$/ })
        .first(),
      resultTable
        .locator("th, td")
        .filter({ hasText: /^(標準偏差|Std Dev)$/ })
        .first(),
    ];
    await highlightElements(page, statLocators, 3000);

    // ── step-H: まとめ ────────────────────────────────────────────────────
    rec.addCue(
      "列と統計量の組み合わせが一覧で確認できます",
      "View all column-statistic combinations at a glance",
    );
    await page.waitForTimeout(3000);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-09 収録完了");
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
