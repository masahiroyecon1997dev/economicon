/**
 * E2E ストーリー 01: CSV 取り込み → 列メニュー全操作 → データメニュー全操作 → 保存（3 形式）
 *
 * ## 使用ファイル
 * - ユニオン1.csv（数値列: value, 文字列列: category などを想定）
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. アプリ起動待機
 * 2. CSV ファイルをインポート（ファイル選択タブ → ファイルクリック → ダイアログ確認）
 * 3. 列メニューの全 10 操作を実施
 * 4. 左サイドバーのデータメニューで名前変更・複製・削除を実施
 * 5. SaveData ビューで CSV / Excel / Parquet の 3 形式で保存
 */

import { expect, test } from "@playwright/test";
import {
  clickColumnMenuItem,
  clickHeaderMenu,
  closeMessageDialog,
  fillDialogAndSubmit,
  importFile,
  navigateToSampleDir,
  openColumnMenu,
  openTableContextMenu,
  waitForAppReady,
} from "./helpers/appHelpers";

// ---------------------------------------------------------------------------
// テスト用定数
// ---------------------------------------------------------------------------
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1_test";
/** ソート・削除用に使いまわす列（ユニオン1.csv の数値列） */
const TARGET_COL = "value";

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe("01: CSV 取り込み → 列メニュー → データメニュー → 保存", () => {
  // アプリ起動は毎テストで待機（直列実行前提）
  test.beforeEach(async ({ page }) => {
    await waitForAppReady(page);
  });

  // =========================================================================
  // STEP 1: CSV ファイルを取り込む
  // =========================================================================
  test("Step 1: CSV ファイルをインポートする", async ({ page }) => {
    // ファイル選択タブに切り替え
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();

    // サンプルディレクトリへ移動
    await navigateToSampleDir(page);

    // CSV ファイルをインポート
    await importFile(page, CSV_FILE_NAME, TABLE_NAME);

    // DataPreview ビューに遷移し、タブにテーブル名が表示されることを確認
    await expect(page.getByRole("tab", { name: TABLE_NAME })).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 列メニュー — 昇順ソート・降順ソート
  // =========================================================================
  test("Step 2: 列メニュー — 昇順ソート・降順ソート", async ({ page }) => {
    // 前提: Step 1 でインポート済みのデータが存在すること
    // このテストは独立して実行するため、サイドバーからテーブルを開く
    const tableTab = page.getByRole("tab", { name: TABLE_NAME });

    if (!(await tableTab.isVisible())) {
      // サイドバーからテーブルを開く
      const sidebarItem = page
        .getByRole("navigation")
        .getByText(TABLE_NAME, { exact: true });
      if (await sidebarItem.isVisible()) {
        await sidebarItem.click();
      }
    }

    await expect(
      page.getByRole("columnheader", { name: TARGET_COL, exact: true }),
    ).toBeVisible();

    // 昇順ソート
    await openColumnMenu(page, TARGET_COL);
    await clickColumnMenuItem(page, /昇順ソート|Sort Ascending/i);

    // ソート後もテーブルが表示されていることを確認
    await expect(
      page.getByRole("columnheader", { name: TARGET_COL, exact: true }),
    ).toBeVisible();

    // 降順ソート
    await openColumnMenu(page, TARGET_COL);
    await clickColumnMenuItem(page, /降順ソート|Sort Descending/i);

    await expect(
      page.getByRole("columnheader", { name: TARGET_COL, exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 3: 列メニュー — 列名変更
  // =========================================================================
  test("Step 3: 列メニュー — 列名変更（value → value_renamed）", async ({
    page,
  }) => {
    const tableTab = page.getByRole("tab", { name: TABLE_NAME });
    if (!(await tableTab.isVisible())) {
      const sidebarItem = page
        .getByRole("navigation")
        .getByText(TABLE_NAME, { exact: true });
      if (await sidebarItem.isVisible()) await sidebarItem.click();
    }

    await openColumnMenu(page, TARGET_COL);
    await clickColumnMenuItem(page, /列名変更|Rename Column/i);

    // ダイアログで新しい列名を入力して変更
    await fillDialogAndSubmit(page, "value_renamed", /名前を変更|Rename/i);

    // 変更後の列名がヘッダーに表示されること
    await expect(
      page.getByRole("columnheader", { name: "value_renamed", exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 4: 列メニュー — 列の複製
  // =========================================================================
  test("Step 4: 列メニュー — 列の複製（value_renamed を複製）", async ({
    page,
  }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    // Step 3 で名前変更済みの想定。存在確認
    const renamedHeader = page.getByRole("columnheader", {
      name: "value_renamed",
      exact: true,
    });

    // どちらかが存在するはず
    const colName = (await renamedHeader.isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, colName);
    await clickColumnMenuItem(page, /列の複製|Duplicate Column/i);

    // 複製列名の入力ダイアログ
    await fillDialogAndSubmit(page, `${colName}_copy`, /複製|Duplicate/i);

    // 複製された列がヘッダーに表示されること
    await expect(
      page.getByRole("columnheader", { name: `${colName}_copy`, exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 5: 列メニュー — 型変換
  // =========================================================================
  test("Step 5: 列メニュー — 型変換（Float64 → Int64）", async ({ page }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    // 変換対象列を特定（value_renamed or value）
    const headerName = (await page
      .getByRole("columnheader", { name: "value_renamed", exact: true })
      .isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, headerName);
    await clickColumnMenuItem(page, /型変換|Cast Type/i);

    // 型変換ダイアログ: ターゲット型を選択（Int64）して Submit
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // 型選択 combobox
    const typeTrigger = dialog.getByRole("combobox").first();
    await typeTrigger.click();
    const int64Option = page.getByRole("option", { name: /Int64|整数/i });
    await int64Option.waitFor({ state: "visible" });
    await int64Option.click();

    // 新列名（デフォルトのまま Submit）
    await dialog.getByRole("button", { name: /型変換|Cast/i }).click();
    await expect(dialog).toBeHidden();

    // テーブルにまだ列が表示されていること
    await expect(
      page.getByRole("columnheader", { name: headerName, exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 6: 列メニュー — 変換列の追加（対数変換）
  // =========================================================================
  test("Step 6: 列メニュー — 変換列の追加（対数変換）", async ({ page }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    const headerName = (await page
      .getByRole("columnheader", { name: "value_renamed", exact: true })
      .isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, headerName);
    await clickColumnMenuItem(page, /変換列の追加|Add Transform Column/i);

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // 変換方法: 対数（デフォルトまたは選択）
    const methodTrigger = dialog.getByRole("combobox").first();
    await methodTrigger.click();
    const logOption = page.getByRole("option", { name: /対数|Logarithm/i });
    await logOption.waitFor({ state: "visible" });
    await logOption.click();

    // 新列名（デフォルトのまま Add）
    await dialog.getByRole("button", { name: /追加|Add/i }).click();
    await expect(dialog).toBeHidden();
  });

  // =========================================================================
  // STEP 7: 列メニュー — ダミー変数の追加
  // =========================================================================
  test("Step 7: 列メニュー — ダミー変数の追加", async ({ page }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    // ダミー変数は文字列列が望ましいが、数値列でも動作確認
    const headerName = (await page
      .getByRole("columnheader", { name: "value_renamed", exact: true })
      .isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, headerName);
    await clickColumnMenuItem(page, /ダミー変数の追加|Add Dummy Column/i);

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // シングルモードでターゲット値を入力して Add
    const targetInput = dialog.getByRole("textbox").first();
    await targetInput.fill("1");

    await dialog.getByRole("button", { name: /追加|Add/i }).click();
    await expect(dialog).toBeHidden();
  });

  // =========================================================================
  // STEP 8: 列メニュー — ラグ・リード列の追加
  // =========================================================================
  test("Step 8: 列メニュー — ラグ列の追加（periods=-1）", async ({ page }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    const headerName = (await page
      .getByRole("columnheader", { name: "value_renamed", exact: true })
      .isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, headerName);
    await clickColumnMenuItem(
      page,
      /ラグ・リード列の追加|Add Lag\/Lead Column/i,
    );

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // Periods に -1 を入力
    const periodsInput = dialog
      .getByRole("spinbutton")
      .or(dialog.getByRole("textbox").nth(0));
    await periodsInput.fill("-1");

    // 新列名（2番目 textbox）にデフォルト名が入っている想定
    await dialog.getByRole("button", { name: /追加|Add/i }).click();
    await expect(dialog).toBeHidden();
  });

  // =========================================================================
  // STEP 9: 列メニュー — シミュレーション列を追加
  // =========================================================================
  test("Step 9: 列メニュー — シミュレーション列を追加（正規分布）", async ({
    page,
  }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    const headerName = (await page
      .getByRole("columnheader", { name: "value_renamed", exact: true })
      .isVisible())
      ? "value_renamed"
      : TARGET_COL;

    await openColumnMenu(page, headerName);
    await clickColumnMenuItem(
      page,
      /シミュレーション列を追加|Add Simulation Column/i,
    );

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // 列名を入力
    const colNameInput = dialog.getByRole("textbox").first();
    await colNameInput.fill("sim_normal");

    // 分布を正規分布に変更
    const distTrigger = dialog.getByRole("combobox").first();
    await distTrigger.click();
    const normalOption = page.getByRole("option", { name: /正規分布|Normal/i });
    await normalOption.waitFor({ state: "visible" });
    await normalOption.click();

    await dialog.getByRole("button", { name: /追加|Add/i }).click();
    await expect(dialog).toBeHidden();
  });

  // =========================================================================
  // STEP 10: 列メニュー — 列を削除
  // =========================================================================
  test("Step 10: 列メニュー — 列を削除（複製列を削除）", async ({ page }) => {
    const sidebarItem = page
      .getByRole("navigation")
      .getByText(TABLE_NAME, { exact: true });
    if (await sidebarItem.isVisible()) await sidebarItem.click();

    // Step 4 で作成した複製列を削除対象とする
    const copyColName = (await page
      .getByRole("columnheader", { name: "value_renamed_copy", exact: true })
      .isVisible())
      ? "value_renamed_copy"
      : `${TARGET_COL}_copy`;

    // 複製列が存在しない場合は sim_normal を削除
    const colToDelete = (await page
      .getByRole("columnheader", { name: copyColName, exact: true })
      .isVisible())
      ? copyColName
      : "sim_normal";

    await openColumnMenu(page, colToDelete);
    await clickColumnMenuItem(page, /列を削除|Delete Column/i);

    // 確認ダイアログが出たら「削除」をクリック
    const dialog = page.getByRole("dialog");
    if (await dialog.isVisible()) {
      await dialog.getByRole("button", { name: /^削除$|^Delete$/i }).click();
      await expect(dialog).toBeHidden();
    }

    // 削除した列がヘッダーから消えていること
    await expect(
      page.getByRole("columnheader", { name: colToDelete, exact: true }),
    ).toBeHidden();
  });

  // =========================================================================
  // STEP 11: データメニュー — データ名変更
  // =========================================================================
  test("Step 11: データメニュー — データ名変更", async ({ page }) => {
    // サイドバーでコンテキストメニューを開く
    await openTableContextMenu(page, TABLE_NAME);

    // 「データ名を変更」をクリック
    await page
      .getByRole("menuitem", { name: /データ名を変更|Rename Data/i })
      .click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    // 新しい名前を入力（末尾に _v2 を追加）
    const input = dialog.getByRole("textbox");
    await input.fill(`${TABLE_NAME}_v2`);

    await dialog.getByRole("button", { name: /名前を変更|Rename/i }).click();
    await expect(dialog).toBeHidden();

    // サイドバーに新しい名前が表示されること
    await expect(
      page
        .getByRole("navigation")
        .getByText(`${TABLE_NAME}_v2`, { exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 12: データメニュー — データを複製
  // =========================================================================
  test("Step 12: データメニュー — データを複製", async ({ page }) => {
    // Step 11 でリネーム済みのテーブルを対象
    const currentName = `${TABLE_NAME}_v2`;
    await openTableContextMenu(page, currentName);

    await page
      .getByRole("menuitem", { name: /データを複製|Duplicate Data/i })
      .click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    const input = dialog.getByRole("textbox");
    await input.fill(`${TABLE_NAME}_copy`);

    await dialog.getByRole("button", { name: /複製|Duplicate/i }).click();
    await expect(dialog).toBeHidden();

    // サイドバーに複製データが追加されること
    await expect(
      page
        .getByRole("navigation")
        .getByText(`${TABLE_NAME}_copy`, { exact: true }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 13: データメニュー — データを削除（複製データを削除）
  // =========================================================================
  test("Step 13: データメニュー — データを削除（複製データを削除）", async ({
    page,
  }) => {
    const copyName = `${TABLE_NAME}_copy`;
    await openTableContextMenu(page, copyName);

    await page
      .getByRole("menuitem", { name: /データを削除|Delete Data/i })
      .click();

    // 削除確認ダイアログ
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: /^削除$|^Delete$/i }).click();
    await expect(dialog).toBeHidden();

    // サイドバーから複製データが消えること
    await expect(
      page.getByRole("navigation").getByText(copyName, { exact: true }),
    ).toBeHidden();
  });

  // =========================================================================
  // STEP 14: 保存 — CSV 形式で保存
  // =========================================================================
  test("Step 14: CSV 形式で保存", async ({ page }) => {
    await _saveCurrentData(page, TABLE_NAME, `${TABLE_NAME}_export.csv`, "csv");
  });

  // =========================================================================
  // STEP 15: 保存 — Excel 形式で保存
  // =========================================================================
  test("Step 15: Excel 形式で保存", async ({ page }) => {
    await _saveCurrentData(
      page,
      TABLE_NAME,
      `${TABLE_NAME}_export.xlsx`,
      "excel",
    );
  });

  // =========================================================================
  // STEP 16: 保存 — Parquet 形式で保存
  // =========================================================================
  test("Step 16: Parquet 形式で保存", async ({ page }) => {
    await _saveCurrentData(
      page,
      TABLE_NAME,
      `${TABLE_NAME}_export.parquet`,
      "parquet",
    );
  });
});

// ---------------------------------------------------------------------------
// 内部ヘルパー
// ---------------------------------------------------------------------------

/**
 * ヘッダーメニューから SaveData ビューに遷移し、指定データを指定フォーマットで保存する。
 *
 * 保存先ディレクトリは SAMPLE_DIR（現在のファイルブラウザが開いていると仮定）。
 */
async function _saveCurrentData(
  page: import("@playwright/test").Page,
  tableName: string,
  fileName: string,
  format: "csv" | "excel" | "parquet",
): Promise<void> {
  // ヘッダーメニュー: ファイル → 保存
  await clickHeaderMenu(page, /ファイル|File/i, /^保存$|^Save$/);

  // SaveData ビューのタイトルを確認
  await expect(
    page.getByRole("heading", { name: /データを保存|Save Data/i }),
  ).toBeVisible();

  // データ名を選択
  const tableNameSelect = page.getByLabel(/保存するデータ|Data to Save/i);
  await tableNameSelect.waitFor({ state: "visible" });
  await tableNameSelect.click();
  await page.getByRole("option", { name: tableName, exact: true }).click();

  // ファイル名を入力（拡張子なし）
  const baseName = fileName.replace(/\.[^.]+$/, "");
  const fileNameInput = page.getByLabel(/ファイル名|File Name/i);
  await fileNameInput.fill(baseName);

  // フォーマットを選択
  const formatLabel =
    format === "csv"
      ? "CSV (.csv)"
      : format === "excel"
        ? "Excel (.xlsx)"
        : "Parquet (.parquet)";
  const formatSelect = page.getByLabel(/ファイル形式|File Format/i);
  await formatSelect.click();
  await page.getByRole("option", { name: formatLabel, exact: true }).click();

  // 保存ボタンをクリック
  await page.getByRole("button", { name: /^保存$|^Save$/i }).click();

  // 上書き確認ダイアログが出た場合は OK をクリック
  const confirmDlg = page.getByRole("dialog");
  if (await confirmDlg.isVisible()) {
    await confirmDlg.getByRole("button", { name: /OK|はい/i }).click();
  }

  // 成功メッセージダイアログを閉じる
  await closeMessageDialog(page);
}
