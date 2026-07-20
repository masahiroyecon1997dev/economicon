/**
 * E2E ストーリー 08: 操作変数法（IV / 2SLS・GMM）
 *
 * ## 使用ファイル
 * - iv_e2e_data.csv
 *   y, x_exog, x_endog, z1, z2 列（N=300 行）
 *   DGP: y = 2 + 3*x_exog + 2*x_endog + eps
 *        x_endog は eta と相関（内生性）, z1/z2 が操作変数（過剰識別）
 *   ※ test/scripts/generate_e2e_iv_data.py で生成
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. iv_e2e_data.csv をインポート
 * 2. 因果推論 → 操作変数法（IV）: y ~ x_exog + [x_endog / z1,z2] で 2SLS 実行 → 結果確認
 * 3. 操作変数法（IV）GMM: 詳細オプションで GMM に切り替えて実行 → 結果確認
 * 4. バリデーション: 内生変数未選択で実行 → エラーメッセージ表示を確認
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
const CSV_FILE_NAME = "iv_e2e_data.csv";
const RUN_ID = `e2e${Date.now().toString(36)}`;
const TABLE_NAME = `iv_${RUN_ID}`;

const DEPENDENT_VAR = "y";
const EXOG_VARS = ["x_exog"];
const ENDOG_VARS = ["x_endog"];
const INSTRUMENTS = ["z1", "z2"];

const STEP_TIMEOUT_MS = 90_000;

let page: Page;

// ---------------------------------------------------------------------------
// ヘルパー: SearchableSelect でオプションを選択する
// ---------------------------------------------------------------------------
async function selectSearchableOption(
  page: Page,
  labelPattern: RegExp,
  optionName: string,
): Promise<void> {
  await page.getByLabel(labelPattern).click();
  const option = page.getByRole("button", { name: optionName, exact: true });
  await option.waitFor({ state: "visible", timeout: 10_000 });
  await option.click();
}

// ---------------------------------------------------------------------------
// ヘルパー: IV フォームの変数を設定する
// ---------------------------------------------------------------------------
async function configureIVForm(
  page: Page,
  formTestId: string = "iv-regression-form",
): Promise<void> {
  const ivForm = page.getByTestId(formTestId);
  await expect(ivForm).toBeVisible();

  // ---- データを選択 ----
  const dataCombobox = ivForm.getByRole("combobox").first();
  await dataCombobox.click();
  const tableOption = page.getByRole("option", {
    name: TABLE_NAME,
    exact: true,
  });
  await tableOption.waitFor({ state: "visible" });
  await tableOption.click();

  // 列情報がロードされるまで待機
  await expect(page.getByText(/列情報を読み込んでいます|Loading/i)).toBeHidden({
    timeout: 15_000,
  });

  // ---- 被説明変数を選択（y）----
  await selectSearchableOption(
    page,
    /被説明変数|Dependent Variable/i,
    DEPENDENT_VAR,
  );

  // ---- 説明変数を選択（x_exog）----
  for (const varName of EXOG_VARS) {
    const checkbox = ivForm.getByRole("checkbox", {
      name: varName,
      exact: true,
    });
    if (!(await checkbox.isChecked())) {
      await checkbox.click();
    }
  }

  // ---- 内生変数を選択（x_endog）----
  for (const varName of ENDOG_VARS) {
    const checkbox = ivForm.getByRole("checkbox", {
      name: varName,
      exact: true,
    });
    if (!(await checkbox.isChecked())) {
      await checkbox.click();
    }
  }

  // ---- 操作変数を選択（z1, z2）----
  for (const varName of INSTRUMENTS) {
    const checkbox = ivForm.getByRole("checkbox", {
      name: varName,
      exact: true,
    });
    if (!(await checkbox.isChecked())) {
      await checkbox.click();
    }
  }
}

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe.serial("08: 操作変数法（IV / 2SLS・GMM）", () => {
  test.beforeAll(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    await clearWorkspaceFromUi(page);
  });

  // =========================================================================
  // STEP 1: iv_e2e_data.csv をインポート
  // =========================================================================
  test("Step 1: iv_e2e_data.csv をインポートする", async () => {
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

    // y 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: DEPENDENT_VAR }),
    ).toBeVisible();

    // x_endog 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: ENDOG_VARS[0] }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 操作変数法（IV）2SLS を実行
  // =========================================================================
  test("Step 2: 操作変数法（2SLS）を実行して結果を確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /因果推論|Causal Inference/i,
      /操作変数法|Instrumental Variables/i,
    );

    // IV フォームのタイトルが表示されること
    await expect(
      page.getByRole("heading", {
        name: /操作変数法|Instrumental Variables/i,
      }),
    ).toBeVisible();

    const ivForm = page.getByTestId("iv-regression-form");
    await expect(ivForm).toBeVisible();

    // 変数設定
    await configureIVForm(page);

    // バッジが存在する場合のみ確認（実装依存のため緩く確認）
    const badge = page.locator(".text-green-600, .text-green-400");
    // バッジ表示は任意確認（存在すればOK）
    const badgeCount = await badge.count();
    if (badgeCount > 0) {
      await expect(badge.first()).toBeVisible();
    }

    // ---- 分析実行 ----
    await ivForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- 結果タブが表示されるまで待機 ----
    await expect(page.getByRole("button", { name: /^IV: y #/i })).toBeVisible({
      timeout: 30_000,
    });

    await page
      .getByRole("button", { name: /^IV: y #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 内生変数（x_endog）の係数行が表示されること
    await expect(
      page.getByRole("cell", { name: ENDOG_VARS[0], exact: true }).first(),
    ).toBeVisible();

    // 外生変数（x_exog）の係数行が表示されること
    await expect(
      page.getByRole("cell", { name: EXOG_VARS[0], exact: true }).first(),
    ).toBeVisible();

    // 観測数が表示されること
    await expect(page.getByText(/観測数|Observations/i)).toBeVisible();
  });

  // =========================================================================
  // STEP 3: 操作変数法（IV）GMM で再実行
  // =========================================================================
  test("Step 3: GMM オプションに切り替えて再実行する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    // 操作変数法メニューを再度開く（フォームタブは既存のものが再利用される）
    await clickHeaderMenu(
      page,
      /因果推論|Causal Inference/i,
      /操作変数法|Instrumental Variables/i,
    );

    const ivForm = page.getByTestId("iv-regression-form");
    await expect(ivForm).toBeVisible();

    // 変数設定
    await configureIVForm(page);

    // ---- 詳細オプションを開く ----
    const advancedOptionsToggle = page.getByRole("button", {
      name: /詳細オプション|Advanced Options/i,
    });
    // 詳細オプションが既に開いている場合は閉じてから再開く必要はないが、
    // 閉じているときは開く
    if (await advancedOptionsToggle.isVisible()) {
      // AdvancedOptionsCard のトグル状態を確認して開く
      const optionsContent = page.getByLabel(/推定手法|Estimation Method/i);
      const isOptionsOpen = await optionsContent.isVisible().catch(() => false);
      if (!isOptionsOpen) {
        await advancedOptionsToggle.click();
      }
    }

    // ---- ivMethod を GMM に変更 ----
    // Radix UI Select のトリガーを label 経由でクリック
    const ivMethodTrigger = page.getByLabel(/推定手法|Estimation Method/i);
    await ivMethodTrigger.waitFor({ state: "visible", timeout: 10_000 });
    await ivMethodTrigger.click();

    const gmmOption = page.getByRole("option", { name: /GMM/i });
    await gmmOption.waitFor({ state: "visible", timeout: 10_000 });
    await gmmOption.click();

    // GMM 重み行列フィールドが表示されること
    await expect(page.getByLabel(/GMM.*重み|GMM.*Weight/i)).toBeVisible({
      timeout: 5_000,
    });

    // ---- 分析実行 ----
    await ivForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- 結果タブが表示されるまで待機（2つ目の IV 結果）----
    await expect(page.getByRole("button", { name: /^IV: y #2/i })).toBeVisible({
      timeout: 30_000,
    });

    await page
      .getByRole("button", { name: /^IV: y #2/i })
      .first()
      .click();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 内生変数（x_endog）の係数行が表示されること
    await expect(
      page.getByRole("cell", { name: ENDOG_VARS[0], exact: true }).first(),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 4: バリデーション — 内生変数未選択
  // =========================================================================
  test("Step 4: 内生変数を選択しないで実行するとエラーが表示される", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /因果推論|Causal Inference/i,
      /操作変数法|Instrumental Variables/i,
    );

    const ivForm = page.getByTestId("iv-regression-form");
    await expect(ivForm).toBeVisible();

    // ---- データを選択 ----
    const dataCombobox = ivForm.getByRole("combobox").first();
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

    // ---- 被説明変数のみ選択し内生変数は選ばない ----
    await selectSearchableOption(
      page,
      /被説明変数|Dependent Variable/i,
      DEPENDENT_VAR,
    );

    // 操作変数だけ選択（内生変数は未選択）
    for (const varName of INSTRUMENTS) {
      const checkbox = ivForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 内生変数を選択せずに実行 ----
    await ivForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- バリデーションエラーが表示されること ----
    await expect(
      page.getByText(
        /内生変数を1つ以上|Please select at least one endogenous/i,
      ),
    ).toBeVisible({ timeout: 10_000 });
  });

  // =========================================================================
  // STEP 5: バリデーション — 操作変数未選択
  // =========================================================================
  test("Step 5: 操作変数を選択しないで実行するとエラーが表示される", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /因果推論|Causal Inference/i,
      /操作変数法|Instrumental Variables/i,
    );

    const ivForm = page.getByTestId("iv-regression-form");
    await expect(ivForm).toBeVisible();

    // ---- データを選択 ----
    const dataCombobox = ivForm.getByRole("combobox").first();
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

    // ---- 被説明変数と内生変数のみ選択（操作変数は未選択）----
    await selectSearchableOption(
      page,
      /被説明変数|Dependent Variable/i,
      DEPENDENT_VAR,
    );

    for (const varName of ENDOG_VARS) {
      const checkbox = ivForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 操作変数を選択せずに実行 ----
    await ivForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // ---- バリデーションエラーが表示されること ----
    await expect(
      page.getByText(
        /操作変数を1つ以上|Please select at least one instrumental/i,
      ),
    ).toBeVisible({ timeout: 10_000 });
  });
});
