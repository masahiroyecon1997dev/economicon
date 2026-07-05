/**
 * E2E ストーリー 05: 可視化
 *
 * ## 使用ファイル
 * - grunfeld.parquet（プロットビューのみ使用）
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. grunfeld.parquet をインポート（プロットビュー用）
 * 2. 可視化 → プロットビュー: データ選択 → 散布図 → X/Y 軸設定 → 描画確認
 * 3. 可視化 → 分布プレビュー: タブ切替 → 分布タイプ変更 → パラメータスライダー → 描画確認
 * 4. 可視化 → 信頼区間シミュレーション: スライダー操作 → 再生/停止 → プロット表示確認
 * 5. 可視化 → 漸近正規性シミュレーション: サンプルサイズ変更 → 誤差タイプ変更 → 描画確認
 * 6. 可視化 → 一致性シミュレーション: スライダー操作 → 再生/停止 → プロット表示確認
 * 7. 可視化 → 不偏性シミュレーション: スライダー操作 → 再生/停止 → プロット表示確認
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
const TABLE_NAME = `grunfeld_vis_${RUN_ID}`;
const STEP_TIMEOUT_MS = 90_000;

let page: Page;

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe
  .serial("05: 可視化（プロットビュー・分布プレビュー・各シミュレーション）", () => {
  test.beforeAll(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    await clearWorkspaceFromUi(page);
  });

  // =========================================================================
  // STEP 1: grunfeld.parquet をインポート（プロットビュー用）
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

    await expect(page.getByRole("button", { name: TABLE_NAME })).toBeVisible();
  });

  // =========================================================================
  // STEP 2: 可視化 → プロットビュー
  // =========================================================================
  test("Step 2: プロットビューで散布図を描画する（value vs invest）", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /^プロットビュー$|^Plot View$/i,
    );

    await expect(
      page.getByRole("heading", { name: /^プロットビュー$|^Plot View$/i }),
    ).toBeVisible();

    // ---- データを選択 ----
    const tableSelect = page.getByTestId("plot-view-table-select");
    await tableSelect.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    // 列情報がロードされるまで待機
    await expect(page.getByTestId("plot-view-loading-columns")).toBeHidden({
      timeout: 15_000,
    });

    // ---- 散布図を選択（デフォルト）----
    await expect(page.getByTestId("plot-type-scatter")).toBeVisible();

    // ---- X 軸に "value" を選択 ----
    const xSelect = page.getByTestId("plot-view-x-column");
    await xSelect.click();
    const xOption = page.getByRole("option", { name: "value", exact: true });
    await xOption.waitFor({ state: "visible" });
    await xOption.click();

    // ---- Y 軸に "invest" を選択 ----
    const ySelect = page.getByTestId("plot-view-y-column");
    await ySelect.click();
    const yOption = page.getByRole("option", {
      name: "invest",
      exact: true,
    });
    await yOption.waitFor({ state: "visible" });
    await yOption.click();

    // プロットパネルが表示され、空の状態オーバーレイが消えること
    await expect(page.getByTestId("plot-view-panel")).toBeVisible();
    await expect(page.getByTestId("plot-view-empty")).toBeHidden({
      timeout: 15_000,
    });

    // ---- ヒストグラムへ切替 ----
    await page.getByTestId("plot-type-histogram").click();
    // Y 軸選択が不要になり empty state が消えること
    await expect(page.getByTestId("plot-view-empty")).toBeHidden({
      timeout: 15_000,
    });
  });

  // =========================================================================
  // STEP 3: 可視化 → 分布プレビュー
  // =========================================================================
  test("Step 3: 分布プレビューで分布タイプを変更しプロットを確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /分布プレビュー|Distribution Preview/i,
    );

    // 分布プレビューコンテナが表示されること
    await expect(page.getByTestId("distribution-preview")).toBeVisible();

    // ---- 「連続分布」タブが表示されていることを確認（デフォルト）----
    await expect(
      page.getByRole("tab", { name: /連続分布|Continuous/i }),
    ).toBeVisible();

    // ---- 正規分布（デフォルト）のプロットが描画されること ----
    await expect(
      page.getByTestId("distribution-preview-plot-area"),
    ).toBeVisible();

    // ロードが終わることを確認
    await expect(page.getByText(/分布を計算しています/i)).toBeHidden({
      timeout: 15_000,
    });

    // ---- 分布タイプを「一様分布」に変更 ----
    const uniformRadio = page.getByRole("radio", { name: /一様分布|Uniform/i });
    await uniformRadio.waitFor({ state: "visible" });
    await uniformRadio.click();

    // パラメータスライダーが更新されること（param-slider-low が存在する）
    await expect(page.getByTestId("param-slider-low")).toBeVisible({
      timeout: 5_000,
    });

    // ---- 「離散分布」タブに切替 ----
    await page.getByRole("tab", { name: /離散分布|Discrete/i }).click();

    // 二項分布ラジオボタンが表示されること
    await expect(
      page.getByRole("radio", { name: /^(二項分布|Binomial)$/i }),
    ).toBeVisible();

    // ---- 「CDF / CMF」タブに切替 ----
    await page.getByRole("button", { name: /CDF \/ CMF/i }).click();

    // プロットエリアが引き続き表示されること
    await expect(
      page.getByTestId("distribution-preview-plot-area"),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 4: 可視化 → 信頼区間シミュレーション
  // =========================================================================
  test("Step 4: 信頼区間シミュレーションを再生して結果を確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /信頼区間シミュレーション|Confidence Interval Sim/i,
    );

    await expect(
      page.getByRole("heading", {
        name: /信頼区間シミュレーション|Confidence Interval Sim/i,
      }),
    ).toBeVisible();

    // ---- 試行回数スライダーを確認 ----
    await expect(page.getByTestId("trials-slider")).toBeVisible();

    // ---- サンプルサイズスライダーを確認 ----
    await expect(
      page
        .getByTestId("confidence-interval-sim")
        .getByTestId("sample-size-slider"),
    ).toBeVisible();

    // ---- 信頼水準 95% ラジオを確認（デフォルト）----
    const level95Radio = page.getByRole("radio", { name: /95%/ }).first();
    await expect(level95Radio).toBeVisible();

    // ---- シミュレーション結果のロード完了を待機 ----
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // 再生ボタンが有効になるまで待機
    const playBtn = page
      .getByTestId("confidence-interval-sim")
      .getByTestId("animation-play-btn");
    await expect(playBtn).toBeEnabled({ timeout: 15_000 });

    // ---- 再生 ----
    await playBtn.click();

    // 一時停止ボタンが表示されること（アニメーション中）
    await expect(page.getByTestId("animation-pause-btn")).toBeVisible({
      timeout: 5_000,
    });

    // ---- 一時停止 ----
    await page.getByTestId("animation-pause-btn").click();

    // 再生ボタンが戻ること
    await expect(page.getByTestId("animation-play-btn")).toBeVisible({
      timeout: 5_000,
    });

    // ---- 横棒プロット・折れ線プロットが表示されること ----
    await expect(page.getByTestId("ci-bar-area")).toBeVisible();
    await expect(page.getByTestId("ci-line-area")).toBeVisible();

    // ---- 「分散 CI」タブに切替 ----
    await page.getByRole("tab", { name: /分散 CI|Variance/i }).click();

    // 真の分散スライダーが表示されること
    await expect(page.getByTestId("true-variance-slider")).toBeVisible();
  });

  // =========================================================================
  // STEP 5: 可視化 → 漸近正規性シミュレーション
  // =========================================================================
  test("Step 5: 漸近正規性シミュレーションでサンプルサイズ・誤差タイプを変更する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /漸近正規性シミュレーション|Asymptotic Normality/i,
    );

    await expect(
      page.getByRole("heading", {
        name: /漸近正規性シミュレーション|Asymptotic Normality/i,
      }),
    ).toBeVisible();

    // 漸近正規性コンテナが表示されること
    await expect(page.getByTestId("asymptotic-normality")).toBeVisible();

    // ---- デフォルトのシミュレーション結果がロードされるまで待機 ----
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // ---- サンプルサイズを 500 に変更（ラジオボタン）----
    const size500Radio = page.getByRole("radio", { name: /^1000$/ });
    await size500Radio.waitFor({ state: "visible" });
    await size500Radio.click();

    // 再ロード完了を待機
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // ---- 誤差タイプを「コーシー誤差（厚裾）」に変更 ----
    const cauchyRadio = page.getByRole("radio", {
      name: /コーシー誤差|Cauchy/i,
    });
    await cauchyRadio.click();

    // コーシー注意書きが表示されること
    await expect(page.getByTestId("cauchy-notice")).toBeVisible({
      timeout: 5_000,
    });

    // 再ロード完了を待機
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // ---- プロットエリアが表示されること ----
    await expect(
      page.getByTestId("asymptotic-normality-plot-area"),
    ).toBeVisible();

    // ---- 真の回帰係数 β スライダーを確認 ----
    await expect(page.getByTestId("true-beta-slider")).toBeVisible();

    // ---- 正規誤差に戻す ----
    const normalRadio = page.getByRole("radio", {
      name: /正規誤差|Normal/i,
    });
    await normalRadio.click();
  });

  // =========================================================================
  // STEP 6: 可視化 → 一致性シミュレーション
  // =========================================================================
  test("Step 6: 一致性シミュレーションを再生して収束を確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /一致性シミュレーション|Consistency/i,
    );

    await expect(
      page.getByRole("heading", {
        name: /一致性シミュレーション|Consistency/i,
      }),
    ).toBeVisible();

    // 一致性コンテナが表示されること
    await expect(page.getByTestId("consistency")).toBeVisible();

    // ---- 外生性ラジオを確認（デフォルト「外生性成立」）----
    const exogenousRadio = page.getByRole("radio", {
      name: /外生性成立|Exogenous/i,
    });
    await expect(exogenousRadio).toBeVisible();
    await expect(exogenousRadio).toBeChecked();

    // ---- n_max スライダーを確認 ----
    await expect(page.getByTestId("n-max-slider")).toBeVisible();

    // ---- シミュレーション結果ロード完了を待機 ----
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // 再生ボタンが有効になるまで待機
    const playBtn = page
      .getByTestId("consistency")
      .getByTestId("animation-play-btn");
    await expect(playBtn).toBeEnabled({ timeout: 15_000 });

    // ---- 再生 ----
    await playBtn.click();

    // 一時停止ボタンが表示されること
    await expect(page.getByTestId("animation-pause-btn")).toBeVisible({
      timeout: 5_000,
    });

    // ---- 一時停止 ----
    await page.getByTestId("animation-pause-btn").click();

    // 再生ボタンが戻ること
    await expect(
      page.getByTestId("consistency").getByTestId("animation-play-btn"),
    ).toBeVisible({
      timeout: 5_000,
    });

    // ---- プロットエリアが表示されること ----
    await expect(page.getByTestId("consistency-plot-area")).toBeVisible();

    // ---- 内生性ありに切替 ----
    const endogenousRadio = page.getByRole("radio", {
      name: /内生性あり|Endogenous/i,
    });
    await endogenousRadio.click();

    // 内生性の強さスライダーが表示されること
    await expect(page.getByTestId("endogeneity-strength-slider")).toBeVisible({
      timeout: 5_000,
    });
  });

  // =========================================================================
  // STEP 7: 可視化 → 不偏性シミュレーション
  // =========================================================================
  test("Step 7: 不偏性シミュレーションを再生してヒストグラムを確認する", async () => {
    test.setTimeout(STEP_TIMEOUT_MS);

    await clickHeaderMenu(
      page,
      /^可視化$|^Visualization$/i,
      /不偏性シミュレーション|Unbiasedness/i,
    );

    await expect(
      page.getByRole("heading", {
        name: /不偏性シミュレーション|Unbiasedness/i,
      }),
    ).toBeVisible();

    // 不偏性コンテナが表示されること
    await expect(page.getByTestId("unbiasedness")).toBeVisible();

    // ---- 各スライダーが表示されること ----
    await expect(
      page.getByTestId("unbiasedness").getByTestId("num-trials-slider"),
    ).toBeVisible();
    await expect(
      page.getByTestId("unbiasedness").getByTestId("sample-size-slider"),
    ).toBeVisible();
    await expect(
      page.getByTestId("unbiasedness").getByTestId("true-beta-slider"),
    ).toBeVisible();
    await expect(
      page.getByTestId("unbiasedness").getByTestId("error-variance-slider"),
    ).toBeVisible();

    // ---- シミュレーション結果ロード完了を待機 ----
    await expect(page.getByText(/シミュレーション実行中/i)).toBeHidden({
      timeout: 30_000,
    });

    // 再生ボタンが有効になるまで待機
    const playBtn = page
      .getByTestId("unbiasedness")
      .getByTestId("animation-play-btn");
    await expect(playBtn).toBeEnabled({ timeout: 15_000 });

    // ---- 再生 ----
    await playBtn.click();

    // 一時停止ボタンが表示されること
    await expect(
      page.getByTestId("unbiasedness").getByTestId("animation-pause-btn"),
    ).toBeVisible({
      timeout: 5_000,
    });

    // ---- 一時停止 ----
    await page
      .getByTestId("unbiasedness")
      .getByTestId("animation-pause-btn")
      .click();

    // 再生ボタンが戻ること
    await expect(
      page.getByTestId("unbiasedness").getByTestId("animation-play-btn"),
    ).toBeVisible({
      timeout: 5_000,
    });

    // ---- ヒストグラム・折れ線プロットエリアが表示されること ----
    await expect(
      page.getByTestId("unbiasedness").getByTestId("unbiasedness-hist-area"),
    ).toBeVisible();
    await expect(
      page.getByTestId("unbiasedness").getByTestId("unbiasedness-line-area"),
    ).toBeVisible();
  });
});
