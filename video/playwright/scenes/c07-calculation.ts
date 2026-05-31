/**
 * C-07 計算列の追加 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. ユニオン1.csv をインポート（録画前）
 *   2. データ → 計算 でフォームを開く
 *   3. 対象データ・新列名・計算式を入力して「計算を実行」
 *   4. 結果列が追加されたテーブルを確認
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c07
 *
 * 出力:
 *   captured/c07/frames/0001.jpg … NNNN.jpg
 *   captured/c07/meta.json
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

const SCENE_ID = "c07";
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1";
const NEW_COL_NAME = "amount_doubled";
/** {列名} 形式の計算式 */
const FORMULA = "{amount} * 2";

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
    // ── 録画前: ワークスペースリセット → CSV インポート ──────────────────
    await resetWorkspace(page);
    await navigateToSampleDir(page);

    const fileRow = page.getByRole("row", { name: CSV_FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await fileRow.click();

    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });
    const nameInput = importDialog.getByRole("textbox").first();
    await nameInput.fill(TABLE_NAME);
    await importDialog
      .getByRole("button", { name: /^インポート$|^Import$/ })
      .click();
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // ── 録画開始 ────────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: テーブルを確認 ────────────────────────────────────────────
    rec.addCue(
      "計算式を使って新しい列を追加できます",
      "You can add a new column using a formula expression",
    );
    await page.waitForTimeout(1500);

    // ── step-B: データ → 計算 へ遷移 ─────────────────────────────────────
    rec.addCue(
      "「データ」→「計算」を選択します",
      "Select 'Data' → 'Calculate'",
    );
    const dataMenuBtn = page.getByRole("banner").getByRole("button", {
      name: /^データ$|^Data$/i,
    });
    await humanClick(page, dataMenuBtn, 400);

    const calcItem = page.getByRole("menuitem", {
      name: /^計算$|^Calculate$/i,
    });
    await calcItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, calcItem, 1000);

    await page
      .getByRole("heading", {
        name: /計算式でカラムを追加|Add Column.*Calculation/i,
      })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: 対象データを選択 ─────────────────────────────────────────
    rec.addCue(
      `対象データに「${TABLE_NAME}」を選択します`,
      `Select '${TABLE_NAME}' as the target data`,
    );
    const dataTrigger = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await humanClick(page, dataTrigger, 400);

    const targetOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await targetOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, targetOption, 800);

    // 列情報のロード待機
    await page
      .getByText(/列情報を読み込んでいます|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // ── step-D: 新しいカラム名を入力 ─────────────────────────────────────
    rec.addCue(
      "新しいカラム名を入力します",
      "Enter the name for the new column",
    );
    const newColInput = page
      .getByLabel(/新しいカラム名|New Column Name/i)
      .first()
      .or(page.getByPlaceholder(/total_revenue/i));
    await newColInput.fill(NEW_COL_NAME);
    await page.waitForTimeout(300);

    // ── step-E: 計算式を入力 ─────────────────────────────────────────────
    rec.addCue(
      `「${FORMULA}」の式を入力します（列名は {} で囲みます）`,
      `Enter the formula '${FORMULA}' — wrap column names in {}`,
    );
    const formulaTextarea = page.getByPlaceholder(/計算式を入力/);
    await formulaTextarea.waitFor({ state: "visible", timeout: 5_000 });
    await formulaTextarea.fill(FORMULA);
    await page.waitForTimeout(600);

    // ── step-F: 計算を実行 ───────────────────────────────────────────────
    rec.addCue("「計算を実行」をクリックします", "Click 'Execute Calculation'");
    const runBtn = page.getByRole("button", {
      name: /計算を実行|Execute Calculation/i,
    });
    await humanClick(page, runBtn, 500);

    // 結果テーブルに新列が表示されるまで待機
    const resultHeader = page.getByRole("columnheader", { name: NEW_COL_NAME });
    await resultHeader.waitFor({ state: "visible", timeout: 30_000 });

    // ── step-G: 結果を確認 ───────────────────────────────────────────────
    rec.addCue(
      `「${NEW_COL_NAME}」列が追加されました`,
      `The '${NEW_COL_NAME}' column has been added`,
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultHeader], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-07 収録完了");
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
