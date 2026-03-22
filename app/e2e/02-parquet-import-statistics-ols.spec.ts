/**
 * E2E ストーリー 02: Parquet 取り込み → 基本統計量 → 最小二乗法（OLS）
 *
 * ## 使用ファイル
 * - grunfeld.parquet（invest, value, capital, firm, year 列）
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. アプリ起動待機
 * 2. Parquet ファイルをインポート
 * 3. 基本分析 → 基本統計量: invest, value, capital を対象に mean/std_dev を計算
 * 4. 線形回帰 → 最小二乗法: invest ~ value + capital で OLS を実行し結果を確認
 */

import { expect, test } from "@playwright/test";
import {
  clickHeaderMenu,
  closeMessageDialog,
  importFile,
  navigateToSampleDir,
} from "./helpers/appHelpers";
import { setupTauriApp } from "./helpers/setupHelpers";

// ---------------------------------------------------------------------------
// テスト用定数
// ---------------------------------------------------------------------------
const PARQUET_FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";

const DEPENDENT_VAR = "invest";
const EXPLANATORY_VARS = ["value", "capital"];

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe("02: Parquet 取り込み → 基本統計量 → OLS", () => {
  // =========================================================================
  // STEP 1: Parquet ファイルをインポート
  // =========================================================================
  test("Step 1: Parquet ファイルをインポートする", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();

    await navigateToSampleDir(page);

    // Parquet ファイルをインポート（データ名は grunfeld のまま）
    await importFile(page, PARQUET_FILE_NAME, TABLE_NAME);

    // DataPreview ビューに遷移し、タブにテーブル名が表示されること
    await expect(page.getByRole("button", { name: TABLE_NAME })).toBeVisible();

    // テーブルヘッダーに invest 列が表示されること
    await expect(
      page.getByRole("columnheader", { name: DEPENDENT_VAR }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 基本分析 → 基本統計量
  // =========================================================================
  test("Step 2: 基本統計量を計算する（mean・std_dev）", async ({
    playwright,
  }) => {
    const page = await setupTauriApp(playwright);
    // 前提: Step 1 でインポート済みのデータが存在すること
    // ヘッダーメニューから BasicAnalysis → BasicStatistics へ遷移
    await clickHeaderMenu(
      page,
      /基本分析|Basic Analysis/i,
      /基本統計量|Basic Statistics/i,
    );

    // DescriptiveStatistics ビューのタイトルを確認
    await expect(
      page.getByRole("heading", { name: /基本統計量|Descriptive Statistics/i }),
    ).toBeVisible();

    // ---- データ選択 ----
    const dataSelectTrigger = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await dataSelectTrigger.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // ---- 列を選択（invest, value, capital を個別にチェック）----
    // 列一覧がロードされてから選択
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading column info/i),
    ).toBeHidden({
      timeout: 15_000,
    });

    for (const col of [DEPENDENT_VAR, ...EXPLANATORY_VARS]) {
      const checkbox = page.getByRole("checkbox", { name: col });
      if (await checkbox.isVisible()) {
        if (!(await checkbox.isChecked())) {
          await checkbox.click();
        }
      }
    }

    // ---- 統計量を選択（mean, std_dev）----
    for (const stat of [/^平均$|^Mean$/i, /^標準偏差$|^Std Dev$/i]) {
      const checkbox = page.getByRole("checkbox", { name: stat });
      if (await checkbox.isVisible()) {
        if (!(await checkbox.isChecked())) {
          await checkbox.click();
        }
      }
    }

    // ---- 計算ボタンをクリック ----
    await page.getByRole("button", { name: /計算する|Calculate/i }).click();

    // ---- 結果テーブルの表示を確認 ----
    // 結果テーブルが表示されること
    const resultTable = page.getByRole("table");
    await expect(resultTable).toBeVisible({ timeout: 30_000 });

    // invest の行が結果に含まれること
    await expect(page.getByRole("cell", { name: DEPENDENT_VAR })).toBeVisible();

    // 数値が表示されていること（0 以上の任意の数値）
    // セルに数値が少なくとも 1 つ以上存在することを確認
    const cells = resultTable.getByRole("cell");
    const count = await cells.count();
    expect(count).toBeGreaterThan(1);
  });

  // =========================================================================
  // STEP 3: 線形回帰 → 最小二乗法（OLS）
  // =========================================================================
  test("Step 3: 最小二乗法（OLS）を実行して結果を確認する", async ({
    playwright,
  }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニューから Linear Regression → OLS へ遷移
    await clickHeaderMenu(
      page,
      /線形回帰|Linear Regression/i,
      /最小二乗法|Ordinary Least Squares/i,
    );

    // LinearRegressionForm ビューのタイトルを確認
    await expect(
      page.getByRole("tab", {
        name: /分析設定\(最小二乗法\)|Analysis Settings\(OLS\)/i,
      }),
    ).toBeVisible();

    // ---- データ選択 ----
    const dataCombobox = page.getByRole("combobox").first();
    await dataCombobox.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // ---- 被説明変数を選択 ----
    // 「被説明変数」というラベルの隣の combobox
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    const dependentSection = page
      .locator("div")
      .filter({ hasText: /^被説明変数|Dependent Variable/ })
      .last();
    const dependentRadio = dependentSection.getByRole("radio").first();
    await dependentRadio.click();
    const dependentOption = page.getByRole("radio", {
      name: DEPENDENT_VAR,
      exact: true,
    });
    await dependentOption.waitFor({ state: "visible" });
    await dependentOption.click();

    // ---- 説明変数を選択（value, capital）----
    const explanatorySection = page
      .locator("div")
      .filter({ hasText: /^説明変数|Explanatory Variables/ })
      .last();

    for (const varName of EXPLANATORY_VARS) {
      const varCheckbox = explanatorySection.getByRole("checkbox", {
        name: varName,
      });
      if (await varCheckbox.isVisible()) {
        if (!(await varCheckbox.isChecked())) {
          await varCheckbox.click();
        }
      } else {
        // combobox 形式の場合
        const triggerBtn = explanatorySection.getByRole("button").last();
        await triggerBtn.click();
        const option = page.getByRole("option", { name: varName, exact: true });
        await option.waitFor({ state: "visible" });
        await option.click();
      }
    }

    // Dropdown を閉じる
    await page.keyboard.press("Escape");

    // ---- 分析実行 ----
    await page.getByRole("button", { name: /分析実行|Run Analysis/i }).click();

    // ---- 結果タブが表示されるまで待機 ----
    // 結果 1（または Result 1）タブが追加されること
    await expect(
      page.getByRole("tab", { name: /結果 1|Result 1/i }),
    ).toBeVisible({ timeout: 30_000 });

    // 結果タブをクリック
    await page.getByRole("tab", { name: /結果 1|Result 1/i }).click();

    // ---- 結果内容の確認 ----
    // 調整済み R² が表示されること
    await expect(page.getByText(/調整済みR²|Adjusted R\u00B2/i)).toBeVisible();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable).toBeVisible();

    // 被説明変数（invest）が係数テーブル or 概要に表示されること
    await expect(page.getByText(DEPENDENT_VAR).first()).toBeVisible();

    // 説明変数（value, capital）の行が係数テーブルに含まれること
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }),
      ).toBeVisible();
    }

    // F値、p値、観測数 などのモデル統計量が表示されること
    await expect(page.getByText(/F値|F.value|F-value/i)).toBeVisible();
    await expect(page.getByText(/観測数|Observations/i)).toBeVisible();
  });

  // =========================================================================
  // STEP 4: Parquet 形式で保存
  // =========================================================================
  test("Step 4: Parquet 形式で保存する", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: ファイル → 保存
    await clickHeaderMenu(page, /ファイル|File/i, /^保存$|^Save$/);

    await expect(
      page.getByRole("heading", { name: /データを保存|Save Data/i }),
    ).toBeVisible();

    // データ名を選択
    const tableNameSelect = page.getByLabel(/保存するデータ|Data to Save/i);
    await tableNameSelect.waitFor({ state: "visible" });
    await tableNameSelect.click();
    await page.getByRole("option", { name: TABLE_NAME, exact: true }).click();

    // ファイル名
    const fileNameInput = page.getByLabel(/ファイル名|File Name/i);
    await fileNameInput.fill(`${TABLE_NAME}_exported`);

    // Parquet 形式を選択
    const formatSelect = page.getByLabel(/ファイル形式|File Format/i);
    await formatSelect.click();
    await page
      .getByRole("option", { name: "Parquet (.parquet)", exact: true })
      .click();

    // 保存
    await page.getByRole("button", { name: /^保存$|^Save$/i }).click();

    // 成功メッセージを閉じる
    await closeMessageDialog(page);
  });
});
