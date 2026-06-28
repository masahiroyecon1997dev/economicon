/**
 * E2E ストーリー 04: 基本分析（拡張）
 *
 * ## 使用ファイル
 * - grunfeld.parquet（invest, value, capital, firm, year 列）
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. grunfeld.parquet をインポート
 * 2. 基本分析 → 相関行列: 列選択 → 実行 → 結果テーブルタブ表示
 * 3. 基本分析 → グループ別統計量: 2ステップウィザード → 実行 → 結果テーブルタブ表示
 * 4. 基本分析 → 信頼区間: 列・統計量タイプ選択 → 実行 → 結果タブ表示
 * 5. 基本分析 → 仮説検定: サンプル設定 → 実行 → 結果タブ表示
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
const PARQUET_FILE_NAME = "grunfeld.parquet";
const RUN_ID = `e2e${Date.now().toString(36)}`;
const TABLE_NAME = `grunfeld_${RUN_ID}`;
const CORR_TABLE_NAME = `corr_result_${RUN_ID}`;
const GROUP_TABLE_NAME = `group_result_${RUN_ID}`;
const STEP_TIMEOUT_MS = 90_000;

let page: Page;

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe
  .serial("04: 基本分析拡張（相関行列・グループ別統計量・信頼区間・仮説検定）", () => {
  test.beforeAll(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    await clearWorkspaceFromUi(page);
  });

  // =========================================================================
  // STEP 1: grunfeld.parquet をインポート
  // =========================================================================
  test("Step 1: grunfeld.parquet をインポートする", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();
    await navigateToSampleDir(page);

    await importFile(page, PARQUET_FILE_NAME, TABLE_NAME);

    // DataPreview ビューに遷移し、テーブルタブが表示されること
    await expect(page.getByRole("button", { name: TABLE_NAME })).toBeVisible();

    // invest 列ヘッダーが表示されること
    await expect(
      page.getByRole("columnheader", { name: "invest" }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 基本分析 → 相関行列
  // =========================================================================
  test("Step 2: 相関行列を作成する（invest・value・capital）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /基本分析|Basic Analysis/i,
      /相関行列|Correlation Matrix/i,
    );

    await expect(
      page.getByRole("heading", { name: /相関行列|Correlation Matrix/i }),
    ).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = page.getByRole("combobox").first();
    await dataSelect.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading column/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 列を選択（invest, value, capital）----
    for (const col of ["invest", "value", "capital"]) {
      const checkbox = page.getByRole("checkbox", { name: col });
      await checkbox.waitFor({ state: "visible" });
      if (!(await checkbox.isChecked())) {
        await checkbox.click();
      }
    }

    // ---- 出力データ名を入力 ----
    const outputInput = page
      .getByLabel(/出力データ名|Output Data/i)
      .first()
      .or(page.getByPlaceholder(/correlation_matrix/i));
    await outputInput.fill(CORR_TABLE_NAME);

    // ---- 作成する ----
    await page.getByRole("button", { name: /^作成する$|^Run$/i }).click();

    // 結果テーブルのサイドバーボタンが表示されること
    await expect(
      page.getByRole("button", { name: CORR_TABLE_NAME }),
    ).toBeVisible({ timeout: 30_000 });
  });

  // =========================================================================
  // STEP 3: 基本分析 → グループ別統計量（シングルページフォーム）
  // =========================================================================
  test("Step 3: グループ別統計量を作成する（firm でグループ化 → invest 集計）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /基本分析|Basic Analysis/i,
      /グループ別統計量|Group Statistics/i,
    );

    await expect(
      page.getByRole("heading", { name: /グループ別統計量|Group Statistics/i }),
    ).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = page.getByRole("combobox").first();
    await dataSelect.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(
      page.getByTestId("group-statistics-loading-columns"),
    ).toBeHidden({ timeout: 15_000 });

    const roleMatrix = page.getByTestId("group-statistics-role-matrix");
    await expect(roleMatrix).toBeVisible();

    // ---- "firm" 列 → グループキー に割り当て ----
    const firmRow = roleMatrix
      .locator(":scope > div.app-scrollbar > div")
      .filter({ hasText: "firm" })
      .filter({ has: page.getByRole("button", { name: /グループキー/ }) })
      .first();
    await firmRow.getByRole("button", { name: /グループキー/ }).click();

    // ---- "invest" 列 → 集計列 に割り当て ----
    const investRow = roleMatrix
      .locator(":scope > div.app-scrollbar > div")
      .filter({ hasText: "invest" })
      .filter({ has: page.getByRole("button", { name: /集計列/ }) })
      .first();
    await investRow.getByRole("button", { name: /集計列/ }).click();

    // ---- 出力データ名を入力（上部の InputText）----
    const outputInput = page.getByTestId("group-statistics-new-table-name");
    await outputInput.fill(GROUP_TABLE_NAME);

    // ---- 作成する ----
    await page.getByRole("button", { name: /^作成する$|^Run$/i }).click();

    // 結果テーブルのサイドバーボタンが表示されること
    await expect(
      page.getByRole("button", { name: GROUP_TABLE_NAME }),
    ).toBeVisible({ timeout: 30_000 });
  });

  // =========================================================================
  // STEP 4: 基本分析 → 信頼区間
  // =========================================================================
  test("Step 4: 信頼区間を計算する（invest 列・平均・95%）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /基本分析|Basic Analysis/i,
      /^信頼区間$|^Confidence Interval$/i,
    );

    await expect(
      page.getByRole("heading", { name: /^信頼区間$|^Confidence Interval$/i }),
    ).toBeVisible();

    // ---- データを選択 ----
    const dataSelect = page.getByRole("combobox").first();
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

    // ---- 列を選択（invest）----
    const columnSelect = page.getByRole("combobox").nth(1);
    await columnSelect.click();
    const columnOption = page.getByRole("option", {
      name: "invest",
      exact: true,
    });
    await columnOption.waitFor({ state: "visible" });
    await columnOption.click();

    // ---- 統計量タイプを選択（平均）----
    const statTypeSelect = page.getByRole("combobox").nth(2);
    await statTypeSelect.click();
    const meanOption = page.getByRole("option", {
      name: /平均（t分布）|Mean/i,
    });
    await meanOption.waitFor({ state: "visible" });
    await meanOption.click();

    // ---- 信頼水準 95% が選択されていることを確認（デフォルト）----
    // デフォルトは "ConfidenceLevelModeSelect" で 0.95 が選択されている
    // 明示的に 95% ラジオボタンを選択
    const level95Radio = page.getByRole("radio", { name: /95%/ });
    if (await level95Radio.isVisible()) {
      await level95Radio.check();
    }

    // ---- 計算する ----
    await page.getByRole("button", { name: /^計算する$|^Calculate$/i }).click();

    // 結果タブが表示されること（"invest の mean 信頼区間 #1"）
    await expect(
      page.getByRole("button", { name: /invest の mean 信頼区間 #/i }),
    ).toBeVisible({ timeout: 30_000 });

    // 結果タブをクリックして p 値の表示を確認
    await page
      .getByRole("button", { name: /invest の mean 信頼区間 #/i })
      .first()
      .click();

    // 信頼区間の下限・上限が表示されること
    await expect(page.getByText(/下限|Lower/i).first()).toBeVisible();
    await expect(page.getByText(/上限|Upper/i).first()).toBeVisible();
  });

  // =========================================================================
  // STEP 5: 基本分析 → 仮説検定
  // =========================================================================
  test("Step 5: 仮説検定を実行する（t 検定・1 群・invest 列）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /基本分析|Basic Analysis/i,
      /^仮説検定$|^Hypothesis Test$/i,
    );

    await expect(
      page.getByRole("heading", { name: /仮説検定|Hypothesis Test/i }),
    ).toBeVisible();

    // t 検定がデフォルト選択されていることを確認（SELECT で "t 検定" が選択中）
    const testTypeSelect = page.getByRole("combobox").first();
    await expect(testTypeSelect).toContainText(/t 検定|t-test/i);

    // ---- サンプル 1: データを選択 ----
    const sampleSection = page.getByTestId("statistical-test-sample-0");
    await expect(sampleSection).toBeVisible();

    const dataSelect = sampleSection.getByRole("combobox").first();
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

    // ---- 列を選択（invest）----
    const columnSelect = sampleSection.getByRole("combobox").last();
    await columnSelect.click();
    const columnOption = page.getByRole("option", {
      name: "invest",
      exact: true,
    });
    await columnOption.waitFor({ state: "visible" });
    await columnOption.click();

    // ---- 検定を実行 ----
    await page
      .getByRole("button", { name: /^検定を実行$|^Run Test$/i })
      .click();

    // 結果タブが表示されること（"t-test（1群） #1"）
    await expect(
      page.getByRole("button", { name: /t-test（1群） #/i }),
    ).toBeVisible({ timeout: 30_000 });

    // 結果タブをクリックして検定統計量・p 値の表示を確認
    await page
      .getByRole("button", { name: /t-test（1群） #/i })
      .first()
      .click();

    await expect(page.getByText(/検定統計量|Statistic/i).first()).toBeVisible();
    await expect(page.getByText(/p 値|P.?[Vv]alue/i).first()).toBeVisible();
  });
});
