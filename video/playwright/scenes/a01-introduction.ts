/**
 * A-01 紹介動画 — Playwright 収録スクリプト
 *
 * 2 つのクリップを順番に収録する:
 *   1. a01-import : CSV インポート → テーブル表示（シーン 3: 約 20 秒）
 *   2. a01-ols    : OLS 線形回帰 → 結果表示（シーン 4: 約 20 秒）
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:a01
 *
 * 出力:
 *   captured/a01-import/frames/0001.jpg … NNNN.jpg + meta.json
 *   captured/a01-ols/frames/0001.jpg … NNNN.jpg + meta.json
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

/** インポート・OLS デモで共通使用するファイル */
const PARQUET_FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
const OLS_DEPENDENT = "invest";
const OLS_EXPLANATORY = ["value", "capital"];

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];
type AppContext = Awaited<ReturnType<typeof connectToApp>>["context"];

/**
 * ファイルブラウザで SAMPLE_DIR まで降りていく。
 * app/e2e/helpers/appHelpers.ts の navigateFileBrowserToDir と同ロジック。
 */
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

/**
 * ワークスペースをリセットしてインポート画面に戻す。
 * c09-descriptive-statistics.ts と同ロジック。
 */
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
// クリップ 1: CSV インポート
// ---------------------------------------------------------------------------

async function recordImportClip(
  context: AppContext,
  page: AppPage,
): Promise<void> {
  console.log("\n📼 CLIP 1: Parquet インポート 収録開始");

  // ── 録画開始 ──────────────────────────────────────────────────────────────
  const rec = await Recorder.create(context, page, "a01-import");
  await rec.start();
  console.log("  ▶ 録画開始");

  // インポート画面で少し待機（視聴者にアプリを見せる）
  rec.addCue(
    "Economicon のインポート画面です",
    "This is the Economicon import screen",
  );
  await page.waitForTimeout(1500);

  // ── SAMPLE_DIR へ移動 ──────────────────────────────────────────────────────
  rec.addCue("サンプルフォルダに移動します", "Navigating to the sample folder");
  await navigateToSampleDir(page);
  await page.waitForTimeout(500);

  // ── Parquet ファイルを選択 ────────────────────────────────────────────────
  rec.addCue(
    "grunfeld.parquet を選択します",
    "Select grunfeld.parquet to import",
  );
  const fileRow = page.getByRole("row", { name: PARQUET_FILE_NAME });
  await fileRow.waitFor({ state: "visible", timeout: 15_000 });
  await humanClick(page, fileRow, 800);

  // ── インポートダイアログを確認 ─────────────────────────────────────────────
  const importDialog = page.getByRole("dialog");
  await importDialog.waitFor({ state: "visible", timeout: 10_000 });

  rec.addCue(
    "設定を確認して「インポート」をクリックします",
    "Confirm settings and click 'Import'",
  );

  const importBtn = importDialog.getByRole("button", {
    name: /^インポート$|^Import$/,
  });
  await humanClick(page, importBtn, 2000);
  await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

  // ── テーブル表示を確認 ─────────────────────────────────────────────────────
  // インポート後に表示されるテーブルを待機（名前は問わない）
  const resultTable = page.getByRole("table").or(page.getByRole("grid"));
  await resultTable.waitFor({ state: "visible", timeout: 20_000 }).catch(() => {
    // テーブルが表示されない場合もタイムアウトを無視して続行
  });

  rec.addCue(
    "データがテーブルとして表示されました",
    "Data is now displayed as a table",
  );
  await page.waitForTimeout(3000);

  // テーブルヘッダーを強調
  const tableEl = page.getByRole("table").first();
  if (await tableEl.isVisible()) {
    await highlightElements(page, [tableEl], 2500);
  }

  const info = await rec.stop();
  console.log(
    `  ✅ CLIP 1 完了: ${info.totalFrames} フレーム, ${(info.durationMs / 1000).toFixed(1)}s`,
  );
}

// ---------------------------------------------------------------------------
// クリップ 2: OLS 回帰
// ---------------------------------------------------------------------------

async function recordOlsClip(
  context: AppContext,
  page: AppPage,
): Promise<void> {
  console.log("\n📼 CLIP 2: OLS 回帰 収録開始");

  // ── 録画前準備: ワークスペースリセット ──────────────────────────────────
  await resetWorkspace(page);

  // ── 録画前準備: grunfeld.parquet をインポート ──────────────────────────
  console.log("  ⏳ grunfeld.parquet をインポート中（録画前）...");
  await navigateToSampleDir(page);

  const parquetRow = page.getByRole("row", { name: PARQUET_FILE_NAME });
  await parquetRow.waitFor({ state: "visible", timeout: 15_000 });
  await parquetRow.click();

  const importDialog = page.getByRole("dialog");
  await importDialog.waitFor({ state: "visible", timeout: 10_000 });
  await importDialog
    .getByRole("button", { name: /^インポート$|^Import$/ })
    .click();
  await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

  await page
    .getByRole("button", { name: TABLE_NAME })
    .waitFor({ state: "visible", timeout: 15_000 });
  await page.waitForTimeout(800);
  console.log("  ✅ インポート完了");

  // ── 録画開始 ──────────────────────────────────────────────────────────────
  const rec = await Recorder.create(context, page, "a01-ols");
  await rec.start();
  console.log("  ▶ 録画開始");

  // ── OLS メニューへ ────────────────────────────────────────────────────────
  rec.addCue(
    "「線形回帰」→「最小二乗法（OLS）」を選択します",
    "Select 'Linear Regression' → 'Ordinary Least Squares (OLS)'",
  );

  const regressionMenuBtn = page.getByRole("banner").getByRole("button", {
    name: /線形回帰|Linear Regression/i,
  });
  await humanClick(page, regressionMenuBtn, 500);

  const olsItem = page.getByRole("menuitem", {
    name: /最小二乗法|Ordinary Least Squares/i,
  });
  await olsItem.waitFor({ state: "visible", timeout: 5_000 });
  await humanClick(page, olsItem, 1000);

  await page
    .getByRole("heading", { name: /最小二乗法|Ordinary Least Squares/i })
    .waitFor({ state: "visible", timeout: 10_000 });

  // ── データ選択 ────────────────────────────────────────────────────────────
  rec.addCue("分析するテーブルを選択します", "Select the table to analyze");
  const dataCombobox = page.getByRole("combobox").first();
  await humanClick(page, dataCombobox, 400);

  const tableOption = page.getByRole("option", {
    name: TABLE_NAME,
    exact: true,
  });
  await tableOption.waitFor({ state: "visible", timeout: 10_000 });
  await humanClick(page, tableOption, 1000);

  await page
    .getByText(/列情報を読み込んでいます|Loading/i)
    .waitFor({ state: "hidden", timeout: 15_000 })
    .catch(() => {});

  // ── 被説明変数を選択 ──────────────────────────────────────────────────────
  rec.addCue(
    `被説明変数に「${OLS_DEPENDENT}」を選択します`,
    `Select '${OLS_DEPENDENT}' as the dependent variable`,
  );
  const dependentSelect = page.getByLabel(/被説明変数|Dependent Variable/i);
  await humanClick(page, dependentSelect, 400);

  const dependentOption = page.getByRole("option", {
    name: OLS_DEPENDENT,
    exact: true,
  });
  await dependentOption.waitFor({ state: "visible", timeout: 10_000 });
  await humanClick(page, dependentOption, 800);

  // ── 説明変数を選択 ────────────────────────────────────────────────────────
  rec.addCue(
    `説明変数に「${OLS_EXPLANATORY.join("」「")}」を選択します`,
    `Select '${OLS_EXPLANATORY.join("', '")}' as explanatory variables`,
  );
  for (const varName of OLS_EXPLANATORY) {
    const varCheckbox = page.getByRole("checkbox", {
      name: varName,
      exact: true,
    });
    if (await varCheckbox.isVisible()) {
      await humanClick(page, varCheckbox, 350);
    }
  }
  await page.waitForTimeout(500);

  // ── 分析実行 ──────────────────────────────────────────────────────────────
  rec.addCue(
    "「分析実行」をクリックして OLS を実行します",
    "Click 'Run Analysis' to execute OLS",
  );
  const runBtn = page.getByRole("button", {
    name: /分析実行|Run Analysis/i,
  });
  await humanClick(page, runBtn, 500);

  // 結果タブが表示されるまで待機
  const resultTab = page.getByRole("button", {
    name: new RegExp(`^OLS: ${OLS_DEPENDENT}`, "i"),
  });
  await resultTab.waitFor({ state: "visible", timeout: 30_000 });

  // 結果タブをクリック
  await humanClick(page, resultTab, 1000);

  // ── 結果を確認 ────────────────────────────────────────────────────────────
  rec.addCue(
    "OLS の推定結果が表示されました",
    "OLS estimation results are displayed",
  );
  await page.waitForTimeout(2000);

  // 係数テーブルを強調
  const coeffTable = page.getByRole("table").first();
  if (await coeffTable.isVisible()) {
    rec.addCue(
      "係数・標準誤差・p 値が一覧で確認できます",
      "Coefficients, standard errors, and p-values are listed",
    );
    await highlightElements(page, [coeffTable], 3000);
  }

  // 調整済み R² テキストを強調
  const r2Text = page.getByText(/調整済みR²|Adjusted R\u00B2/i).first();
  if (await r2Text.isVisible()) {
    rec.addCue(
      "調整済み R² でモデルの当てはまりを確認できます",
      "Adjusted R² shows the goodness of fit",
    );
    await highlightElements(page, [r2Text], 2000);
  }

  await page.waitForTimeout(1000);

  const info = await rec.stop();
  console.log(
    `  ✅ CLIP 2 完了: ${info.totalFrames} フレーム, ${(info.durationMs / 1000).toFixed(1)}s`,
  );
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();
  try {
    // ── 初期リセット ─────────────────────────────────────────────────────────
    await resetWorkspace(page);

    // ── CLIP 1: CSV インポート ─────────────────────────────────────────────
    await recordImportClip(context, page);

    // ── CLIP 2: OLS 回帰 ──────────────────────────────────────────────────
    await recordOlsClip(context, page);

    console.log("\n✅ A-01 収録完了");
    console.log("   出力先: video/playwright/captured/a01-import/");
    console.log("           video/playwright/captured/a01-ols/");
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ 収録失敗:", err);
  process.exit(1);
});
