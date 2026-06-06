/**
 * C-21 分析結果の出力（LaTeX/Markdown） — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. grunfeld.parquet をインポート（録画前）
 *   2. 線形回帰 → 最小二乗法 で OLS を実行
 *   3. 結果タブから「出力...」ボタンをクリック
 *   4. フォーマット選択（LaTeX）→ プレビュー確認 → コピー
 *   5. Markdown に切り替えて再確認
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c21
 *
 * 出力:
 *   captured/c21/frames/0001.jpg … NNNN.jpg
 *   captured/c21/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  highlightElements,
  humanClick,
  maskDirUsername,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c21";
const FILE_NAME = "grunfeld.parquet";
const TABLE_NAME = "grunfeld";
const DEPENDENT_VAR = "invest";
const EXPLANATORY_VARS = ["value", "capital"];

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];

async function navigateToSampleDir(page: AppPage): Promise<void> {
  const fileSelectTab = page.getByRole("tab", {
    name: /ファイル選択|Select File/i,
  });
  if (await fileSelectTab.isVisible()) await fileSelectTab.click();
  const sep = path.sep;
  const segments = SAMPLE_DIR.split(sep).filter((s) => s.length > 0);
  for (const segment of segments) {
    const folderRow = page
      .getByRole("row", { name: segment })
      .filter({ hasNot: page.locator('[data-file="true"]') });
    if (await folderRow.isVisible()) {
      await folderRow.click();
      await page.waitForTimeout(300);
    }
  }
}

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
    await navigateToSampleDir(page);
    await maskDirUsername(page);

    const fileRow = page.getByRole("row", { name: FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await fileRow.click();
    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });
    await importDialog.getByRole("textbox").first().fill(TABLE_NAME);
    await importDialog
      .getByRole("button", { name: /^インポート$|^Import$/ })
      .click();
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // ── OLS を実行（録画前）────────────────────────────────────────────────
    const regrMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /^線形回帰$|^Linear Regression$/i });
    await regrMenu.click();
    const olsItem = page.getByRole("menuitem", {
      name: /最小二乗法|Ordinary Least Squares/i,
    });
    await olsItem.waitFor({ state: "visible" });
    await olsItem.click();

    await page
      .getByRole("heading", { name: /最小二乗法|Ordinary Least Squares/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // データ選択
    const dataCombobox = page.getByRole("combobox").first();
    await dataCombobox.click();
    const tableOption = page.getByRole("option", {
      name: TABLE_NAME,
      exact: true,
    });
    await tableOption.waitFor({ state: "visible" });
    await tableOption.click();

    await page
      .getByText(/列情報を読み込んでいます|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // 被説明変数
    const depSelect = page.getByLabel(/被説明変数|Dependent Variable/i);
    await depSelect.click();
    const depOpt = page.getByRole("option", {
      name: DEPENDENT_VAR,
      exact: true,
    });
    await depOpt.waitFor({ state: "visible" });
    await depOpt.click();

    // 説明変数
    for (const varName of EXPLANATORY_VARS) {
      const cb = page.getByRole("checkbox", { name: varName, exact: true });
      if (!(await cb.isChecked())) await cb.click();
    }

    // 分析実行
    await page.getByRole("button", { name: /分析実行|Run Analysis/i }).click();
    await page
      .getByRole("button", { name: new RegExp(`OLS: ${DEPENDENT_VAR} #1`) })
      .waitFor({ state: "visible", timeout: 30_000 });
    await page
      .getByRole("button", { name: new RegExp(`OLS: ${DEPENDENT_VAR} #1`) })
      .click();
    await page.waitForTimeout(500);

    // ── 録画開始 ──────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: 概要 ───────────────────────────────────────────────────────
    rec.addCue(
      "分析結果を LaTeX や Markdown 形式でエクスポートできます",
      "Export analysis results in LaTeX or Markdown format",
    );
    await page.waitForTimeout(1500);

    // ── step-B: 出力ダイアログを開く ─────────────────────────────────────
    rec.addCue(
      "結果パネルの「出力...」ボタンをクリックします",
      "Click the 'Output...' button on the results panel",
    );
    const outputBtn = page.getByRole("button", {
      name: /^出力\.\.\.$|^Output\.\.\./i,
    });
    await outputBtn.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, outputBtn, 500);

    const outputDialog = page.getByRole("dialog");
    await outputDialog.waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: LaTeX フォーマットを選択 ─────────────────────────────────
    rec.addCue(
      "フォーマットに「LaTeX」を選択します",
      "Select 'LaTeX' as the output format",
    );
    const formatTrigger = outputDialog
      .getByLabel(/フォーマット|Format/i)
      .or(outputDialog.getByRole("combobox").first());
    await humanClick(page, formatTrigger, 400);
    const latexOpt = page.getByRole("option", {
      name: /^LaTeX$/i,
      exact: true,
    });
    await latexOpt.waitFor({ state: "visible" });
    await humanClick(page, latexOpt, 400);
    await page.waitForTimeout(400);

    // プレビューボタンをクリック（あれば）
    const previewBtn = outputDialog.getByRole("button", {
      name: /^プレビュー$|^Preview$/i,
    });
    if (await previewBtn.isVisible({ timeout: 2_000 })) {
      await humanClick(page, previewBtn, 400);
    }

    await outputDialog
      .getByText(/生成中|Loading/i)
      .waitFor({ state: "hidden", timeout: 20_000 })
      .catch(() => {});
    await page.waitForTimeout(1000);

    rec.addCue(
      "LaTeX 形式の回帰テーブルがプレビューされています",
      "LaTeX regression table is previewed",
    );
    await highlightElements(page, [outputDialog], 2000);

    // ── step-D: コピーボタン ──────────────────────────────────────────────
    rec.addCue(
      "「コピー」ボタンでクリップボードにコピーします",
      "Click 'Copy' to copy to the clipboard",
    );
    const copyBtn = outputDialog.getByRole("button", {
      name: /^コピー$|^Copy$/i,
    });
    await humanClick(page, copyBtn, 400);

    // コピー完了メッセージ
    const copiedMsg = outputDialog.getByText(/コピーしました|Copied/i);
    await copiedMsg
      .waitFor({ state: "visible", timeout: 5_000 })
      .catch(() => {});
    await page.waitForTimeout(1000);

    // ── step-E: Markdown に切替 ───────────────────────────────────────────
    rec.addCue(
      "フォーマットを「Markdown」に切り替えます",
      "Switch the format to 'Markdown'",
    );
    await humanClick(page, formatTrigger, 400);
    const mdOpt = page.getByRole("option", {
      name: /^Markdown$/i,
      exact: true,
    });
    await mdOpt.waitFor({ state: "visible" });
    await humanClick(page, mdOpt, 400);

    if (await previewBtn.isVisible({ timeout: 2_000 })) {
      await humanClick(page, previewBtn, 400);
    }

    await outputDialog
      .getByText(/生成中|Loading/i)
      .waitFor({ state: "hidden", timeout: 20_000 })
      .catch(() => {});
    await page.waitForTimeout(1000);

    rec.addCue(
      "Markdown 形式でも出力できます",
      "Markdown format is also available",
    );
    await highlightElements(page, [outputDialog], 2000);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-21 収録完了");
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
