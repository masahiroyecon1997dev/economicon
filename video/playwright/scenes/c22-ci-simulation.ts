/**
 * C-22 信頼区間シミュレーション — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. 可視化 → 信頼区間シミュレーション を開く
 *   2. 「平均 CI」タブ（デフォルト）を確認
 *   3. 信頼水準 95%・試行回数 50 を設定
 *   4. アニメーション「再生」ボタンをクリック
 *   5. カバレッジ率の推移グラフをハイライト
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c22
 *
 * 出力:
 *   captured/c22/frames/0001.jpg … NNNN.jpg
 *   captured/c22/meta.json
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

const SCENE_ID = "c22";

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

    // ── step-A: 概要 ───────────────────────────────────────────────────────
    rec.addCue(
      "繰り返しサンプリングで信頼区間のカバレッジを可視化します",
      "Visualize confidence interval coverage via repeated sampling",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 可視化 → 信頼区間シミュレーション ────────────────────────
    rec.addCue(
      "「可視化」→「信頼区間シミュレーション」を選択します",
      "Select 'Visualization' → 'Confidence Interval Simulation'",
    );
    const vizMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /^可視化$|^Visualization$/i });
    await humanClick(page, vizMenu, 400);
    const ciSimItem = page.getByRole("menuitem", {
      name: /信頼区間シミュレーション|Confidence Interval Simulation/i,
    });
    await ciSimItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, ciSimItem, 1000);

    await page
      .getByRole("heading", { name: /信頼区間シミュレーション|Confidence Interval Simulation/i })
      .waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(500);

    // ── step-C: 平均 CI タブ（デフォルト）を確認 ─────────────────────────
    rec.addCue(
      "「平均 CI」タブで母平均の信頼区間シミュレーションを行います",
      "The 'Mean CI' tab simulates confidence intervals for the population mean",
    );
    // デフォルトが平均 CI タブのはずだが明示的にクリック
    const meanCiTab = page.getByRole("tab", { name: /^平均 CI$|^Mean CI$/i });
    if (await meanCiTab.isVisible({ timeout: 3_000 })) {
      await humanClick(page, meanCiTab, 400);
    }
    await page.waitForTimeout(500);

    // ── step-D: 信頼水準・試行回数を設定 ────────────────────────────────
    rec.addCue(
      "信頼水準を 95%、試行回数を 50 に設定します",
      "Set confidence level to 95% and trials to 50",
    );

    // 信頼水準: 0.95 のボタン（ある場合）または スライダー
    const cl95 = page
      .getByRole("radio", { name: /95%/i })
      .or(page.getByRole("button", { name: /95%/i }))
      .first();
    if (await cl95.isVisible({ timeout: 2_000 })) {
      await humanClick(page, cl95, 300);
    }
    await page.waitForTimeout(300);

    // 試行回数スライダー（M）を最小付近に設定（デモ用に小さくする）
    const trialSlider = page
      .getByLabel(/試行回数|Trials/i)
      .first()
      .or(page.locator('input[type="range"]').first());
    if (await trialSlider.isVisible({ timeout: 2_000 })) {
      // HTML input[type=range] の min 値に設定
      await trialSlider.fill("50");
    }
    await page.waitForTimeout(400);

    // ── step-E: アニメーション再生 ────────────────────────────────────────
    rec.addCue(
      "「再生」ボタンでアニメーションを開始します",
      "Click 'Play' to start the animation",
    );
    const playBtn = page.getByRole("button", { name: /^再生$|^Play$/i });
    await playBtn.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, playBtn, 500);

    // アニメーション実行中（3秒待機）
    await page.waitForTimeout(3000);

    rec.addCue(
      "区間が真の値を包含するかをリアルタイムで確認できます",
      "See in real time whether each interval contains the true value",
    );
    await page.waitForTimeout(2000);

    // ── step-F: 結果ハイライト ────────────────────────────────────────────
    // 一時停止
    const pauseBtn = page.getByRole("button", { name: /^一時停止$|^Pause$/i });
    if (await pauseBtn.isVisible({ timeout: 2_000 })) {
      await humanClick(page, pauseBtn, 300);
    }

    rec.addCue(
      "カバレッジ率（信頼水準に近づく様子）が右グラフで確認できます",
      "The right graph shows the coverage rate converging to the confidence level",
    );
    await page.waitForTimeout(2000);

    const plotArea = page
      .locator('[data-testid="plot-div"]')
      .or(page.locator(".js-plotly-plot"))
      .first();
    await highlightElements(page, [plotArea], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-22 収録完了");
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
