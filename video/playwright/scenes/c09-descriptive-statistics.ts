/**
 * C-09 基本統計量 — Playwright キャプチャスクリプト
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
 *   captured/c09/step-01.png … step-06.png
 */

import path from "node:path";

import {
  captureStep,
  connectToApp,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c09";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
/** チェックする列（grunfeld.parquet の数値列） */
const COLUMNS = ["invest", "value", "capital"];
/** 統計量チェックボックス名パターン */
const STAT_PATTERNS: RegExp[] = [/^平均$|^Mean$/i, /^標準偏差$|^Std Dev$/i];
/** 操作後の安定待機 (ms) */
const PAUSE_MS = 800;

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
      await page.waitForTimeout(PAUSE_MS / 2);
    }
  }
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, page } = await connectToApp();

  try {
    // ── ① ワークスペースをリセット ──────────────────────────────────────
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

    // ── ② SAMPLE_DIR へ移動して grunfeld.parquet をインポート ────────────
    await navigateToSampleDir(page);

    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await fileRow.click();

    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });

    // データ名はデフォルト（grunfeld）のまま
    const importBtn = importDialog.getByRole("button", {
      name: /^インポート$|^Import$/,
    });
    await importBtn.click();
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // DataPreview に遷移してテーブルタブが表示されるまで待機
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(PAUSE_MS);

    // ── step-01: データプレビュー（インポート完了状態） ───────────────────
    await captureStep(page, SCENE_ID, 1);
    console.log("  📸 step-01: DataPreview");

    // ── ③ 「基本分析」メニューを開く ─────────────────────────────────────
    const menuBtn = page.getByRole("banner").getByRole("button", {
      name: /基本分析|Basic Analysis/i,
    });
    await menuBtn.click();

    const basicStatsItem = page.getByRole("menuitem", {
      name: /基本統計量|Basic Statistics/i,
    });
    await basicStatsItem.waitFor({ state: "visible", timeout: 5_000 });
    await page.waitForTimeout(PAUSE_MS);

    // ── step-02: 「基本分析」メニューが開いた状態 ─────────────────────────
    await captureStep(page, SCENE_ID, 2);
    console.log("  📸 step-02: メニューが開いた状態");

    // ── ④ 「基本統計量」をクリック ──────────────────────────────────────
    await basicStatsItem.click();

    await page
      .getByRole("heading", { name: /基本統計量|Descriptive Statistics/i })
      .waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(PAUSE_MS);

    // ── step-03: 基本統計量フォームが表示された状態 ────────────────────────
    await captureStep(page, SCENE_ID, 3);
    console.log("  📸 step-03: フォーム初期状態");

    // ── ⑤ テーブルを選択 ────────────────────────────────────────────────
    const dataSelect = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await dataSelect.click();

    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible", timeout: 10_000 });
    await tableOption.click();

    // 列リストのロード完了を待機
    await page
      .getByText(/列情報を読み込んでいます|Loading column info/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {
        // 既にロード済みの場合は無視
      });
    await page.waitForTimeout(PAUSE_MS);

    // ── ⑥ 列を選択 ───────────────────────────────────────────────────────
    for (const col of COLUMNS) {
      const checkbox = page.getByRole("checkbox", { name: col });
      if (await checkbox.isVisible()) {
        if (!(await checkbox.isChecked())) {
          await checkbox.click();
        }
      }
    }
    await page.waitForTimeout(PAUSE_MS);

    // ── step-04: 列が選択された状態 ─────────────────────────────────────
    await captureStep(page, SCENE_ID, 4);
    console.log("  📸 step-04: 列が選択された状態");

    // ── ⑦ 統計量を選択 ───────────────────────────────────────────────────
    for (const pattern of STAT_PATTERNS) {
      const checkbox = page.getByRole("checkbox", { name: pattern });
      if (await checkbox.isVisible()) {
        if (!(await checkbox.isChecked())) {
          await checkbox.click();
        }
      }
    }
    await page.waitForTimeout(PAUSE_MS);

    // ── step-05: 統計量が選択された状態 ─────────────────────────────────
    await captureStep(page, SCENE_ID, 5);
    console.log("  📸 step-05: 統計量が選択された状態");

    // ── ⑧ 「計算する」をクリック ────────────────────────────────────────
    await page.getByRole("button", { name: /^(計算する|Calculate)$/i }).click();

    // 結果テーブルが表示されるまで待機
    await page
      .getByRole("table")
      .waitFor({ state: "visible", timeout: 30_000 });
    await page.waitForTimeout(PAUSE_MS);

    // ── step-06: 結果テーブルが表示された状態 ────────────────────────────
    await captureStep(page, SCENE_ID, 6);
    console.log("  📸 step-06: 結果テーブル");

    console.log("");
    console.log("✅ C-09 キャプチャ完了");
    console.log(`   出力先: video/playwright/captured/${SCENE_ID}/`);
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ キャプチャ失敗:", err);
  process.exit(1);
});
