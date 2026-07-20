/**
 * E2E ストーリー 07: パネルデータ回帰（固定効果法・変量効果法）
 *
 * ## 使用ファイル
 * - panel_e2e_data.csv
 *   entity_id, time_id, x1, x2, y 列（N=10×15=150行）
 *   DGP: y = 1 + 3*x1 - 2*x2 + alpha_i + epsilon
 *   ※ test/scripts/generate_e2e_panel_data.py で生成
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. panel_e2e_data.csv をインポート
 * 2. パネルデータ分析 → 固定効果法（FE）: y ~ x1 + x2, entity_id/time_id を指定して実行 → 結果確認
 * 3. パネルデータ分析 → 変量効果法（RE）: y ~ x1 + x2, entity_id/time_id を指定して実行 → 結果確認
 * 4. FE バリデーション: entityIdColumn 未選択で実行 → エラーメッセージ表示を確認
 */

import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import {
  clearWorkspaceFromUi,
  clickHeaderMenu,
  importFile,
  navigateToSampleDir,
} from "./helpers/appHelpers";
import { setupTauriApp } from "./helpers/setupHelpers";

// ---------------------------------------------------------------------------
// テスト用定数
// ---------------------------------------------------------------------------
const CSV_FILE_NAME = "panel_e2e_data.csv";
const RUN_ID = `e2e${Date.now().toString(36)}`;
const TABLE_NAME = `panel_${RUN_ID}`;

const DEPENDENT_VAR = "y";
const EXPLANATORY_VARS = ["x1", "x2"];
const ENTITY_ID_COL = "entity_id";
const TIME_COL = "time_id";

const STEP_TIMEOUT_MS = 90_000;

let page: Page;

// ---------------------------------------------------------------------------
// ヘルパー: SearchableSelect でオプションを選択する
// ---------------------------------------------------------------------------

/**
 * SearchableSelect トリガーをクリックしてオプションを選択する。
 * Radix UI Popover を使用しているため、オプションはポータルに描画される。
 */
async function selectSearchableOption(
  page: Page,
  labelPattern: RegExp,
  optionName: string,
): Promise<void> {
  // FormField の label が htmlFor でトリガーと紐付いているため getByLabel で取得
  await page.getByLabel(labelPattern).click();
  // ポータル内のオプションボタンを待機・クリック
  const option = page.getByRole("button", { name: optionName, exact: true });
  await option.waitFor({ state: "visible", timeout: 10_000 });
  await option.click();
}

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe.serial("07: パネルデータ回帰（固定効果法・変量効果法）", () => {
  test.beforeAll(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    await clearWorkspaceFromUi(page);
  });

  // =========================================================================
  // STEP 1: panel_e2e_data.csv をインポート
  // =========================================================================
  test("Step 1: panel_e2e_data.csv をインポートする", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();
    await navigateToSampleDir(page);

    await importFile(page, CSV_FILE_NAME, TABLE_NAME);

    // DataPreview ビューに遷移し、テーブルタブが表示されること
    await expect(page.getByRole("button", { name: TABLE_NAME })).toBeVisible();

    // entity_id 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: ENTITY_ID_COL }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: パネルデータ分析 → 固定効果法（FE）
  // =========================================================================
  test("Step 2: 固定効果法（FE）を実行して結果を確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /パネルデータ分析|Panel Data Analysis/i,
      /固定効果法|Fixed Effects/i,
    );

    // FE フォームのタイトルが表示されること
    await expect(
      page.getByRole("heading", { name: /固定効果法|Fixed Effects/i }),
    ).toBeVisible();

    const feForm = page.getByTestId("fe-regression-form");
    await expect(feForm).toBeVisible();

    // ---- データを選択 ----
    const dataCombobox = feForm.getByRole("combobox").first();
    await dataCombobox.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 被説明変数を選択（y）----
    await selectSearchableOption(
      page,
      /被説明変数|Dependent Variable/i,
      DEPENDENT_VAR,
    );

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = feForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 個体ID列を選択（entity_id）----
    await selectSearchableOption(
      page,
      /個体ID列|Entity ID Column/i,
      ENTITY_ID_COL,
    );

    // ---- 時間列を選択（time_id）----
    await selectSearchableOption(page, /時間列|Time Column/i, TIME_COL);

    // ---- 分析実行 ----
    await feForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- 結果タブが表示されるまで待機（"FE: y #1"）----
    await expect(page.getByRole("button", { name: /^FE: y #/i })).toBeVisible({
      timeout: 30_000,
    });

    await page
      .getByRole("button", { name: /^FE: y #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // パネルモデル統計量セクションが表示されること
    await expect(
      page.getByText(/パネルモデル統計量|Panel Model Statistics/i),
    ).toBeVisible();

    // Within R² が表示されること
    await expect(page.getByText(/Within R²/i)).toBeVisible();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 説明変数（x1, x2）の係数行が表示されること
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }

    // F値・観測数が表示されること
    await expect(page.getByText(/F値|F.value|F-value/i)).toBeVisible();
    await expect(page.getByText(/観測数|Observations/i)).toBeVisible();
  });

  // =========================================================================
  // STEP 3: パネルデータ分析 → 変量効果法（RE）
  // =========================================================================
  test("Step 3: 変量効果法（RE）を実行して結果を確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /パネルデータ分析|Panel Data Analysis/i,
      /変量効果法|Random Effects/i,
    );

    // RE フォームのタイトルが表示されること
    await expect(
      page.getByRole("heading", { name: /変量効果法|Random Effects/i }),
    ).toBeVisible();

    const reForm = page.getByTestId("re-regression-form");
    await expect(reForm).toBeVisible();

    // ---- データを選択 ----
    const dataCombobox = reForm.getByRole("combobox").first();
    await dataCombobox.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 被説明変数を選択（y）----
    await selectSearchableOption(
      page,
      /被説明変数|Dependent Variable/i,
      DEPENDENT_VAR,
    );

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = reForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 個体ID列を選択（entity_id）----
    await selectSearchableOption(
      page,
      /個体ID列|Entity ID Column/i,
      ENTITY_ID_COL,
    );

    // ---- 時間列を選択（time_id）----
    await selectSearchableOption(page, /時間列|Time Column/i, TIME_COL);

    // ---- 分析実行 ----
    await reForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- 結果タブが表示されるまで待機（"RE: y #1" 以降）----
    await expect(page.getByRole("button", { name: /^RE: y #/i })).toBeVisible({
      timeout: 30_000,
    });

    await page
      .getByRole("button", { name: /^RE: y #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // パネルモデル統計量セクション（Within R²）が表示されること
    await expect(
      page.getByText(/パネルモデル統計量|Panel Model Statistics/i),
    ).toBeVisible();

    await expect(page.getByText(/Within R²/i)).toBeVisible();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 説明変数（x1, x2）の係数行が表示されること
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }
  });

  // =========================================================================
  // STEP 4: FE バリデーション — entityIdColumn 未選択
  // =========================================================================
  test("Step 4: FE フォームで entityIdColumn 未選択のまま実行するとエラーが表示される", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /パネルデータ分析|Panel Data Analysis/i,
      /固定効果法|Fixed Effects/i,
    );

    const feForm = page.getByTestId("fe-regression-form");
    await expect(feForm).toBeVisible();

    // ---- データを選択 ----
    const dataCombobox = feForm.getByRole("combobox").first();
    await dataCombobox.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 被説明変数のみ選択し entityIdColumn は選ばない ----
    await selectSearchableOption(
      page,
      /被説明変数|Dependent Variable/i,
      DEPENDENT_VAR,
    );

    // ---- entityIdColumn を選択せずに実行 ----
    await feForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- バリデーションエラーが表示されること ----
    await expect(
      page.getByText(/個体ID列を選択|Please select an entity ID column/i),
    ).toBeVisible({ timeout: 10_000 });
  });
});
