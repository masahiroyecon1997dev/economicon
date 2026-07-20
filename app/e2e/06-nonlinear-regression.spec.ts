/**
 * E2E ストーリー 06: 非線形回帰（ロジット・プロビット・トービット）
 *
 * ## 使用ファイル
 * - binary_test_data.csv（const, x1, x2, x3, y_logit, y_probit, y_tobit 列）
 * - tobit_e2e_data.csv（x1, x2, y_left, y_both 列）
 *   ※ test/scripts/generate_e2e_sample_data.py で生成
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. binary_test_data.csv をインポート
 * 2. 非線形回帰 → ロジットモデル: 変数選択 → 分析実行 → 結果タブ表示・係数確認
 * 3. 非線形回帰 → プロビットモデル: 変数選択 → 分析実行 → 結果タブ表示・係数確認
 * 4. tobit_e2e_data.csv をインポート
 * 5. 非線形回帰 → トービットモデル（左打ち切りのみ）: y_left ~ x1 + x2
 * 6. 非線形回帰 → トービットモデル（両側打ち切り）: y_both ~ x1 + x2、right=4.0
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
const CSV_FILE_NAME = "binary_test_data.csv";
const TOBIT_CSV_FILE_NAME = "tobit_e2e_data.csv";
const RUN_ID = `e2e${Date.now().toString(36)}`;
const TABLE_NAME = `binary_${RUN_ID}`;
const TABLE_TOBIT = `tobit_${RUN_ID}`;
const DEPENDENT_LOGIT = "y_logit";
const DEPENDENT_PROBIT = "y_probit";
const DEPENDENT_TOBIT_LEFT = "y_left";
const DEPENDENT_TOBIT_BOTH = "y_both";
const EXPLANATORY_VARS = ["x1", "x2"];
/** tobit_e2e_data.csv の右打ち切り値（data_generators/e2e_tobit.py の RIGHT_CENSORING_LIMIT と一致） */
const TOBIT_RIGHT_CENSORING_LIMIT = "4";
const STEP_TIMEOUT_MS = 90_000;

let page: Page;

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe
  .serial("06: 非線形回帰（ロジット・プロビット・トービット）", () => {
  test.beforeAll(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    await clearWorkspaceFromUi(page);
  });

  // =========================================================================
  // STEP 1: binary_test_data.csv をインポート
  // =========================================================================
  test("Step 1: binary_test_data.csv をインポートする", async () => {
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

    // y_logit 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: DEPENDENT_LOGIT }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 非線形回帰 → ロジットモデル
  // =========================================================================
  test("Step 2: ロジットモデルを推定する（y_logit ~ x1 + x2）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /非線形回帰|Nonlinear Regression/i,
      /ロジットモデル|Logit/i,
    );

    await expect(
      page.getByRole("heading", { name: /ロジットモデル|Logit/i }),
    ).toBeVisible();

    // フォームコンテナが表示されること
    const logitForm = page.getByTestId("logit-regression-form");
    await expect(logitForm).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = logitForm.getByRole("combobox").first();
    await dataSelect.click();
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

    // ---- 被説明変数を選択（y_logit）----
    const dependentSelect = logitForm.getByLabel(
      /被説明変数|Dependent Variable/i,
    );
    await dependentSelect.click();
    const dependentOption = page.getByRole("option", {
      name: DEPENDENT_LOGIT,
      exact: true,
    });
    await dependentOption.waitFor({ state: "visible" });
    await dependentOption.click();

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = logitForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 平均限界効果の計算が有効であることを確認（デフォルト）----
    const marginalEffectsCheckbox = logitForm.getByRole("checkbox", {
      name: /平均限界効果を計算|Marginal Effects/i,
    });
    if (await marginalEffectsCheckbox.isVisible()) {
      await expect(marginalEffectsCheckbox).toBeChecked();
    }

    // ---- 分析実行 ----
    await logitForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // 結果タブが表示されること（"LOGIT: y_logit #1"）
    await expect(
      page.getByRole("button", { name: /^LOGIT: y_logit #/i }),
    ).toBeVisible({ timeout: 30_000 });

    // 結果タブをクリック
    await page
      .getByRole("button", { name: /^LOGIT: y_logit #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // 疑似 R²（McFadden）が表示されること
    await expect(
      page.getByText(/疑似R²|Pseudo.*R|McFadden/i).first(),
    ).toBeVisible();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 説明変数（x1, x2）の係数行が表示されること
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }

    // 平均限界効果セクションが表示されること
    await expect(
      page.getByText(/平均限界効果|Marginal Effect/i).first(),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 3: 非線形回帰 → プロビットモデル
  // =========================================================================
  test("Step 3: プロビットモデルを推定する（y_probit ~ x1 + x2）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /非線形回帰|Nonlinear Regression/i,
      /プロビットモデル|Probit/i,
    );

    await expect(
      page.getByRole("heading", { name: /プロビットモデル|Probit/i }),
    ).toBeVisible();

    // フォームコンテナが表示されること（logit フォームと DOM 共存するため必ずスコープする）
    const probitForm = page.getByTestId("probit-regression-form");
    await expect(probitForm).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = probitForm.getByRole("combobox").first();
    await dataSelect.click();
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

    // ---- 被説明変数を選択（y_probit）----
    // logit フォームにも同一 id="dependent-variable" が存在するためフォームスコープ必須
    const dependentSelect = probitForm.getByLabel(
      /被説明変数|Dependent Variable/i,
    );
    await dependentSelect.click();
    const dependentOption = page.getByRole("option", {
      name: DEPENDENT_PROBIT,
      exact: true,
    });
    await dependentOption.waitFor({ state: "visible" });
    await dependentOption.click();

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = probitForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 分析実行 ----
    await probitForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // 結果タブが表示されること（"PROBIT: y_probit #1"）
    await expect(
      page.getByRole("button", { name: /^PROBIT: y_probit #/i }),
    ).toBeVisible({ timeout: 30_000 });

    // 結果タブをクリック
    await page
      .getByRole("button", { name: /^PROBIT: y_probit #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // 疑似 R²（McFadden）が表示されること
    await expect(
      page.getByText(/疑似R²|Pseudo.*R|McFadden/i).first(),
    ).toBeVisible();

    // 係数テーブルが表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();

    // 説明変数（x1, x2）の係数行が表示されること
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }

    // 平均限界効果セクションが表示されること
    await expect(
      page.getByText(/平均限界効果|Marginal Effect/i).first(),
    ).toBeVisible();

    // 尤度比検定統計量が表示されること
    await expect(
      page.getByText(/尤度比|Likelihood Ratio|LR/i).first(),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 4: tobit_e2e_data.csv をインポート
  // =========================================================================
  test("Step 4: tobit_e2e_data.csv をインポートする", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();
    await navigateToSampleDir(page);

    await importFile(page, TOBIT_CSV_FILE_NAME, TABLE_TOBIT);

    // テーブルタブが表示されること
    await expect(page.getByRole("button", { name: TABLE_TOBIT })).toBeVisible();

    // y_left 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: DEPENDENT_TOBIT_LEFT }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 5: 非線形回帰 → トービットモデル（左打ち切りのみ）
  // =========================================================================
  test("Step 5: トービットモデルを推定する（y_left ~ x1 + x2、左打ち切りのみ）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /非線形回帰|Nonlinear Regression/i,
      /トービットモデル|Tobit/i,
    );

    await expect(
      page.getByRole("heading", { name: /トービットモデル|Tobit/i }),
    ).toBeVisible();

    const tobitForm = page.getByTestId("tobit-regression-form");
    await expect(tobitForm).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = tobitForm.getByRole("combobox").first();
    await dataSelect.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_TOBIT,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 被説明変数を選択（y_left）----
    const dependentSelect = tobitForm.getByLabel(
      /被説明変数|Dependent Variable/i,
    );
    await dependentSelect.click();
    const dependentOption = page.getByRole("option", {
      name: DEPENDENT_TOBIT_LEFT,
      exact: true,
    });
    await dependentOption.waitFor({ state: "visible" });
    await dependentOption.click();

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = tobitForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 打ち切り設定を確認 ----
    // 左打ち切りチェックボックスがデフォルトで有効であること
    const leftCensoringCheckbox = tobitForm.getByRole("checkbox", {
      name: /左側打ち切り|Left censoring/i,
    });
    await expect(leftCensoringCheckbox).toBeChecked();

    // 右打ち切りチェックボックスがデフォルトで無効であること
    const rightCensoringCheckbox = tobitForm.getByRole("checkbox", {
      name: /右側打ち切り|Right censoring/i,
    });
    await expect(rightCensoringCheckbox).not.toBeChecked();

    // ---- 分析実行 ----
    await tobitForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // 結果タブが表示されること（"TOBIT: y_left #1"）
    await expect(
      page.getByRole("button", { name: /^TOBIT: y_left #/i }),
    ).toBeVisible({ timeout: 30_000 });

    await page
      .getByRole("button", { name: /^TOBIT: y_left #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // AIC / BIC が表示されること
    await expect(page.getByText("AIC").first()).toBeVisible();
    await expect(page.getByText("BIC").first()).toBeVisible();

    // 係数テーブルに x1, x2 の行が表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }

    // 診断統計量セクションが表示されること
    await expect(
      page.getByText(/診断統計量|Diagnostics/i).first(),
    ).toBeVisible();

    // σ (Sigma) が表示されること
    await expect(page.getByText(/σ.*Sigma|Sigma/i).first()).toBeVisible();

    // LR 検定セクションが表示されること
    await expect(
      page.getByText(/尤度比検定|Likelihood Ratio Test/i).first(),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 6: 非線形回帰 → トービットモデル（両側打ち切り）
  // =========================================================================
  test("Step 6: トービットモデルを推定する（y_both ~ x1 + x2、両側打ち切り）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /非線形回帰|Nonlinear Regression/i,
      /トービットモデル|Tobit/i,
    );

    await expect(
      page.getByRole("heading", { name: /トービットモデル|Tobit/i }),
    ).toBeVisible();

    // Step 5 のフォームと DOM 共存するためスコープ必須（最後にアクティブなタブで検索）
    const tobitForms = page.getByTestId("tobit-regression-form");
    const tobitForm = tobitForms.last();
    await expect(tobitForm).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = tobitForm.getByRole("combobox").first();
    await dataSelect.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_TOBIT,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 被説明変数を選択（y_both）----
    const dependentSelect = tobitForm.getByLabel(
      /被説明変数|Dependent Variable/i,
    );
    await dependentSelect.click();
    const dependentOption = page.getByRole("option", {
      name: DEPENDENT_TOBIT_BOTH,
      exact: true,
    });
    await dependentOption.waitFor({ state: "visible" });
    await dependentOption.click();

    // ---- 説明変数を選択（x1, x2）----
    for (const varName of EXPLANATORY_VARS) {
      const checkbox = tobitForm.getByRole("checkbox", {
        name: varName,
        exact: true,
      });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 右打ち切りを有効化して値を入力 ----
    const rightCensoringCheckbox = tobitForm.getByRole("checkbox", {
      name: /右側打ち切り|Right censoring/i,
    });
    await expect(rightCensoringCheckbox).not.toBeChecked();
    await rightCensoringCheckbox.click();
    await expect(rightCensoringCheckbox).toBeChecked();

    // 右打ち切り値入力フィールドが表示されること
    const rightLimitInput = tobitForm.locator("#tobit-right-censoring-limit");
    await expect(rightLimitInput).toBeVisible();
    await rightLimitInput.fill(TOBIT_RIGHT_CENSORING_LIMIT);

    // ---- 分析実行 ----
    await tobitForm
      .getByRole("button", { name: /^分析実行$|^Run Analysis$/i })
      .click();

    // 結果タブが表示されること（"TOBIT: y_both #1"）
    await expect(
      page.getByRole("button", { name: /^TOBIT: y_both #/i }),
    ).toBeVisible({ timeout: 30_000 });

    await page
      .getByRole("button", { name: /^TOBIT: y_both #/i })
      .first()
      .click();

    // ---- 結果内容の確認 ----
    // 係数テーブルに x1, x2 の行が表示されること
    const coeffTable = page.getByRole("table");
    await expect(coeffTable.first()).toBeVisible();
    for (const varName of EXPLANATORY_VARS) {
      await expect(
        page.getByRole("cell", { name: varName, exact: true }).first(),
      ).toBeVisible();
    }

    // 診断統計量セクションが表示されること
    await expect(
      page.getByText(/診断統計量|Diagnostics/i).first(),
    ).toBeVisible();

    // 右側打ち切り値（4.0000）が診断統計量に表示されること
    await expect(
      page.getByText(/右側打ち切り|Right Censoring/i).first(),
    ).toBeVisible();

    // Wald 検定セクションが表示されること
    await expect(page.getByText(/Wald/i).first()).toBeVisible();
  });
});
