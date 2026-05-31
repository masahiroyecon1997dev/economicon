/**
 * C-23 OLS 推定量シミュレーション（漸近正規性・一致性・不偏性）
 * Playwright 動画収録スクリプト
 *
 * 収録シナリオ（3機能を連続して収録）:
 *
 *   A. 漸近正規性シミュレーション
 *      - 可視化 → 漸近正規性シミュレーション
 *      - n=500 / 正規誤差 → ヒストグラム確認
 *
 *   B. 一致性シミュレーション
 *      - 可視化 → 一致性シミュレーション
 *      - 外生性成立 → 再生 → β̂ 収束確認
 *
 *   C. 不偏性シミュレーション
 *      - 可視化 → 不偏性シミュレーション
 *      - 再生 → 試行平均収束確認
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c23
 *
 * 出力:
 *   captured/c23/frames/0001.jpg … NNNN.jpg
 *   captured/c23/meta.json
 */

import {
  connectToApp,
  highlightElements,
  humanClick,
  Recorder,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c23";

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];

async function resetWorkspace(page: AppPage): Promise<void> {
  const resetButton = page.getByTestId("left-menu-reset-workspace");
  await resetButton.waitFor({ state: "visible", timeout: 90_000 });
  if (await resetButton.isEnabled()) {
    await resetButton.click();
    const dlg = page.getByRole("dialog").or(page.getByRole("alertdialog"));
    await dlg.waitFor({ state: "visible", timeout: 10_000 });
    await dlg.getByRole("button", { name: /^OK$/i }).click();
    await dlg.waitFor({ state: "hidden", timeout: 10_000 });
  }
  await page
    .getByRole("heading", { name: /ファイルをインポート|Select File/i })
    .waitFor({ state: "visible", timeout: 30_000 });
}

/** 可視化メニューから指定アイテムを開く */
async function openVizMenu(page: AppPage, itemName: RegExp): Promise<void> {
  const vizMenu = page
    .getByRole("banner")
    .getByRole("button", { name: /^可視化$|^Visualization$/i });
  await humanClick(page, vizMenu, 400);
  const item = page.getByRole("menuitem", { name: itemName });
  await item.waitFor({ state: "visible", timeout: 5_000 });
  await humanClick(page, item, 800);
  await page.waitForTimeout(500);
}

/** アニメーション再生して数秒後に一時停止 */
async function playAndPause(
  page: AppPage,
  waitMs: number,
): Promise<void> {
  const playBtn = page.getByRole("button", { name: /^再生$|^Play$/i });
  if (await playBtn.isVisible({ timeout: 3_000 })) {
    await humanClick(page, playBtn, 400);
    await page.waitForTimeout(waitMs);
    const pauseBtn = page.getByRole("button", { name: /^一時停止$|^Pause$/i });
    if (await pauseBtn.isVisible({ timeout: 2_000 })) {
      await humanClick(page, pauseBtn, 300);
    }
  }
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // ── 録画前準備 ─────────────────────────────────────────────────────────
    await resetWorkspace(page);
    await page.waitForTimeout(500);

    // ── 録画開始 ──────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // =========================================================================
    // A. 漸近正規性シミュレーション
    // =========================================================================

    rec.addCue(
      "【漸近正規性】OLS 推定量が大標本で正規分布に収束することを確認します",
      "[Asymptotic Normality] Verify that OLS estimators converge to normality in large samples",
    );
    await page.waitForTimeout(1200);

    rec.addCue(
      "「可視化」→「漸近正規性シミュレーション」を選択します",
      "Select 'Visualization' → 'Asymptotic Normality Simulation'",
    );
    await openVizMenu(
      page,
      /漸近正規性|Asymptotic Normality/i,
    );

    await page
      .getByRole("heading", { name: /漸近正規性|Asymptotic Normality/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // n = 500 を選択
    rec.addCue(
      "サンプルサイズ n = 500 を選択します",
      "Select sample size n = 500",
    );
    const n500 = page.getByRole("radio", { name: "500" });
    if (await n500.isVisible({ timeout: 3_000 })) {
      await humanClick(page, n500, 300);
    }
    await page.waitForTimeout(500);

    // 誤差タイプ: 正規誤差
    const normalErrorRadio = page.getByRole("radio", {
      name: /^正規誤差$|^Normal Error$/i,
    });
    if (await normalErrorRadio.isVisible({ timeout: 2_000 })) {
      await humanClick(page, normalErrorRadio, 300);
    }
    await page.waitForTimeout(1000);

    rec.addCue(
      "標準化された OLS 推定量のヒストグラムが正規分布に近づいています",
      "The histogram of standardized OLS estimators approximates the normal distribution",
    );
    const plotArea = page
      .locator('[data-testid="plot-div"]')
      .or(page.locator(".js-plotly-plot"))
      .first();
    await highlightElements(page, [plotArea], 2500);

    // =========================================================================
    // B. 一致性シミュレーション
    // =========================================================================

    rec.addCue(
      "【一致性】サンプルサイズが増えると推定量が真値に収束することを確認します",
      "[Consistency] Verify that the estimator converges to the true value as n increases",
    );
    await page.waitForTimeout(1200);

    rec.addCue(
      "「可視化」→「一致性シミュレーション」を選択します",
      "Select 'Visualization' → 'Consistency Simulation'",
    );
    await openVizMenu(page, /一致性シミュレーション|Consistency Simulation/i);

    await page
      .getByRole("heading", { name: /一致性|Consistency/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // 外生性成立
    const exogenousRadio = page.getByRole("radio", {
      name: /^外生性成立$|^Exogenous$/i,
    });
    if (await exogenousRadio.isVisible({ timeout: 2_000 })) {
      await humanClick(page, exogenousRadio, 300);
    }
    await page.waitForTimeout(400);

    rec.addCue(
      "アニメーションを再生してサンプルサイズを増やします",
      "Play the animation to increase the sample size",
    );
    await playAndPause(page, 3500);

    rec.addCue(
      "n が大きくなるにつれ β̂ が真値 β₀ に収束しています",
      "β̂ converges to the true value β₀ as n grows",
    );
    await highlightElements(page, [plotArea], 2500);

    // =========================================================================
    // C. 不偏性シミュレーション
    // =========================================================================

    rec.addCue(
      "【不偏性】OLS 推定量の期待値が真のパラメータに等しいことを確認します",
      "[Unbiasedness] Verify that the expected value of OLS estimators equals the true parameter",
    );
    await page.waitForTimeout(1200);

    rec.addCue(
      "「可視化」→「不偏性シミュレーション」を選択します",
      "Select 'Visualization' → 'Unbiasedness Simulation'",
    );
    await openVizMenu(page, /不偏性シミュレーション|Unbiasedness Simulation/i);

    await page
      .getByRole("heading", { name: /不偏性|Unbiasedness/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    await page.waitForTimeout(400);

    rec.addCue(
      "アニメーションを再生します",
      "Start the animation",
    );
    await playAndPause(page, 3500);

    rec.addCue(
      "試行を重ねると推定量の平均が真の β に収束します",
      "As trials accumulate, the average of estimators converges to the true β",
    );
    await highlightElements(page, [plotArea], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-23 収録完了");
    console.log(`   フレーム数: ${info.totalFrames}`);
    console.log(`   長さ: ${(info.durationMs / 1000).toFixed(1)}s`);
    console.log(`   出力先: video/playwright/captured/${SCENE_ID}/`);
  } finally {
    await browser.close();
  }
}

main().catch((err: unknown) => {
  console.error("❌ 収録失敗:", err);
  process.exit(1);
});
