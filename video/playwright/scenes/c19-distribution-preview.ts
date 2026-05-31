/**
 * C-19 確率分布プレビュー — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. 可視化 → 分布プレビュー を開く（データ不要）
 *   2. 連続分布タブ → 正規分布 を確認（デフォルト）
 *   3. パラメータ（平均=0、標準偏差=1）を確認
 *   4. CDF タブに切替 → 累積分布確認
 *   5. 分布を t 分布に変更してプレビュー確認
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c19
 *
 * 出力:
 *   captured/c19/frames/0001.jpg … NNNN.jpg
 *   captured/c19/meta.json
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

const SCENE_ID = "c19";

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
    // ── 録画前準備（ワークスペースリセットのみ、データ不要）─────────────
    await resetWorkspace(page);
    await page.waitForTimeout(500);

    // ── 録画開始 ──────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: 概要 ───────────────────────────────────────────────────────
    rec.addCue(
      "主要な確率分布の密度関数・累積分布関数をプレビューできます",
      "Preview probability density and cumulative distribution functions",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 可視化 → 分布プレビュー ──────────────────────────────────
    rec.addCue(
      "「可視化」→「分布プレビュー」を選択します",
      "Select 'Visualization' → 'Distribution Preview'",
    );
    const vizMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /^可視化$|^Visualization$/i });
    await humanClick(page, vizMenu, 400);
    const distItem = page.getByRole("menuitem", {
      name: /^分布プレビュー$|^Distribution Preview$/i,
    });
    await distItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, distItem, 1000);

    await page
      .getByRole("heading", { name: /分布プレビュー|Distribution Preview/i })
      .waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(1000);

    // ── step-C: 正規分布（デフォルト）の PDF を確認 ──────────────────────
    rec.addCue(
      "正規分布の確率密度関数（PDF）が表示されています",
      "Normal distribution PDF is displayed by default",
    );

    const plotArea = page
      .locator('[data-testid="plot-div"]')
      .or(page.locator(".js-plotly-plot"))
      .or(page.locator("svg").first());
    await page.waitForTimeout(1500);
    await highlightElements(page, [plotArea], 1500);

    // ── step-D: CDF タブへ切替 ────────────────────────────────────────────
    rec.addCue(
      "「CDF / CMF」タブをクリックして累積分布関数を確認します",
      "Click 'CDF / CMF' tab to view the cumulative distribution function",
    );
    const cdfTab = page.getByRole("tab", { name: /CDF|累積/i });
    await humanClick(page, cdfTab, 600);

    await page
      .getByText(/分布を計算しています|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});
    await page.waitForTimeout(1500);
    await highlightElements(page, [plotArea], 1500);

    // ── step-E: PDF タブに戻して t 分布に変更 ────────────────────────────
    rec.addCue(
      "PDF タブに戻し、分布を変更してみます",
      "Return to PDF tab and change the distribution",
    );
    const pdfTab = page.getByRole("tab", { name: /PDF|PMF/i });
    await humanClick(page, pdfTab, 400);
    await page.waitForTimeout(400);

    // 分布セレクタを探して t 分布 または 指数分布に変更
    const distTrigger = page.getByRole("combobox").first();
    await humanClick(page, distTrigger, 400);
    // t_distribution or exponential
    const tDistOpt = page
      .getByRole("option", { name: /^t分布|^t_distribution|^指数分布/i })
      .first();
    if (await tDistOpt.isVisible({ timeout: 3_000 })) {
      await humanClick(page, tDistOpt, 400);
    } else {
      // 別の分布を選択
      const uniformOpt = page.getByRole("option", {
        name: /^一様分布|^Uniform/i,
      });
      if (await uniformOpt.isVisible({ timeout: 3_000 })) {
        await humanClick(page, uniformOpt, 400);
      }
    }

    await page
      .getByText(/分布を計算しています|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});
    await page.waitForTimeout(1500);

    rec.addCue(
      "分布の形状がリアルタイムで更新されます",
      "The distribution shape updates in real time",
    );
    await highlightElements(page, [plotArea], 2000);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-19 収録完了");
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
