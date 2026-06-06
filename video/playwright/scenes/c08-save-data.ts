/**
 * C-08 データの保存 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. ユニオン1.csv をインポート（録画前）
 *   2. ファイル → 保存 を開く
 *   3. CSV 形式で保存
 *   4. Excel 形式で保存
 *   5. Parquet 形式で保存
 *   ※ 保存後ファイルはクリーンアップしない（録画後に手動削除）
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c08
 *
 * 出力:
 *   captured/c08/frames/0001.jpg … NNNN.jpg
 *   captured/c08/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  humanClick,
  maskDirUsername,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c08";
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1";
/** 保存ファイル名（拡張子なし） */
const SAVE_BASE_NAME = "union1_saved";

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];
type Format = "csv" | "excel" | "parquet";

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

/** SaveData 画面に遷移して 1 つのフォーマットで保存する */
async function saveCurrentData(
  page: AppPage,
  rec: Recorder,
  tableName: string,
  baseName: string,
  format: Format,
): Promise<void> {
  const formatLabel =
    format === "csv"
      ? "CSV (.csv)"
      : format === "excel"
        ? "Excel (.xlsx)"
        : "Parquet (.parquet)";
  const formatJa =
    format === "csv" ? "CSV" : format === "excel" ? "Excel" : "Parquet";

  // ファイル → 保存
  const fileMenuBtn = page.getByRole("banner").getByRole("button", {
    name: /ファイル|File/i,
  });
  await humanClick(page, fileMenuBtn, 400);
  const saveItem = page.getByRole("menuitem", { name: /^保存$|^Save$/i });
  await saveItem.waitFor({ state: "visible", timeout: 5_000 });
  await humanClick(page, saveItem, 1000);

  await page
    .getByRole("heading", { name: /データを保存|Save Data/i })
    .waitFor({ state: "visible", timeout: 10_000 });

  // 保存先ディレクトリに移動
  await navigateToSampleDir(page);
  await page.waitForTimeout(500);

  rec.addCue(`${formatJa} 形式で保存します`, `Saving in ${formatJa} format`);

  // データを選択
  const dataLabel = page.getByLabel(/保存するデータ|Data to Save/i);
  await dataLabel.waitFor({ state: "visible", timeout: 10_000 });
  await dataLabel.click();
  const dataOption = page.getByRole("option", { name: tableName, exact: true });
  await dataOption.waitFor({ state: "visible" });
  await humanClick(page, dataOption, 300);

  // ファイル名を入力
  const fileNameInput = page.getByLabel(/ファイル名|File Name/i);
  await fileNameInput.fill(baseName);

  // フォーマットを選択
  const formatSelect = page.getByLabel(/ファイル形式|File Format/i);
  await formatSelect.click();
  const formatOption = page.getByRole("option", {
    name: formatLabel,
    exact: true,
  });
  await formatOption.waitFor({ state: "visible" });
  await humanClick(page, formatOption, 400);
  await page.waitForTimeout(500);

  // 保存ボタンをクリック
  rec.addCue("「保存」ボタンをクリックします", "Click the 'Save' button");
  const saveBtn = page.getByRole("button", { name: /^保存$|^Save$/i });
  await humanClick(page, saveBtn, 500);

  // 上書き確認ダイアログが出た場合
  const confirmDlg = page.getByRole("dialog");
  const isOverwrite = await confirmDlg
    .getByText(/上書き|Overwrite/i)
    .isVisible()
    .catch(() => false);
  if (isOverwrite) {
    await confirmDlg.getByRole("button", { name: /OK|はい/i }).click();
  }

  // 成功ダイアログを閉じる
  const successDlg = page.getByRole("dialog");
  await successDlg.waitFor({ state: "visible", timeout: 30_000 });
  const okBtn = successDlg.getByRole("button", { name: /^OK$/i });
  await okBtn.waitFor({ state: "visible" });
  await humanClick(page, okBtn, 800);
  await successDlg.waitFor({ state: "hidden", timeout: 10_000 });

  rec.addCue(
    `${formatJa} ファイルとして保存されました`,
    `Saved as a ${formatJa} file`,
  );
  await page.waitForTimeout(1500);
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
    await maskDirUsername(page);

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

    // ── step-A: 概要説明 ──────────────────────────────────────────────────
    rec.addCue(
      "3 種類の形式でデータを保存できます",
      "You can save data in three formats: CSV, Excel, and Parquet",
    );
    await page.waitForTimeout(1500);

    // ── PART 1: CSV で保存 ────────────────────────────────────────────────
    await saveCurrentData(
      page,
      rec,
      TABLE_NAME,
      `${SAVE_BASE_NAME}_csv`,
      "csv",
    );

    // ── PART 2: Excel で保存 ──────────────────────────────────────────────
    await saveCurrentData(
      page,
      rec,
      TABLE_NAME,
      `${SAVE_BASE_NAME}_excel`,
      "excel",
    );

    // ── PART 3: Parquet で保存 ────────────────────────────────────────────
    await saveCurrentData(
      page,
      rec,
      TABLE_NAME,
      `${SAVE_BASE_NAME}_parquet`,
      "parquet",
    );

    // ── step-Z: まとめ ───────────────────────────────────────────────────
    rec.addCue(
      "CSV / Excel / Parquet の 3 形式に対応しています",
      "Economicon supports saving in CSV, Excel, and Parquet formats",
    );
    await page.waitForTimeout(2000);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-08 収録完了");
    console.log(`   フレーム数: ${info.totalFrames}`);
    console.log(`   長さ: ${(info.durationMs / 1000).toFixed(1)}s`);
    console.log(`   出力先: video/playwright/captured/${SCENE_ID}/`);
    console.log("");
    console.log(
      "⚠️  保存したファイルをクリーンアップする場合は手動で sample/ から削除してください。",
    );
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ 収録失敗:", err);
  process.exit(1);
});
