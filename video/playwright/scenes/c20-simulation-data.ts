/**
 * C-20 シミュレーションデータ生成 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. データ → データ生成 を開く
 *   2. データ名・行数を入力（100 行）
 *   3. 列設定: 「編集」ボタン → 列名 "x_normal" → 正規分布を選択 → 設定
 *   4. 「データを作成」をクリック
 *   5. 生成されたデータをプレビュー
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c20
 *
 * 出力:
 *   captured/c20/frames/0001.jpg … NNNN.jpg
 *   captured/c20/meta.json
 */

import path from "node:path";

import {
  connectToApp,
  highlightElements,
  humanClick,
  Recorder,
  SAMPLE_DIR,
} from "../helpers/connectToApp.js";

// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

const SCENE_ID = "c20";
const TABLE_NAME = "sim_data";
const COL_NAME = "x_normal";
const ROW_COUNT = "100";

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
      "確率分布から任意のサイズのデータを生成できます",
      "Generate synthetic data from probability distributions",
    );
    await page.waitForTimeout(1500);

    // ── step-B: データ → データ生成 ───────────────────────────────────────
    rec.addCue(
      "「データ」→「データ生成」を選択します",
      "Select 'Data' → 'Data Generation'",
    );
    const dataMenu = page
      .getByRole("banner")
      .getByRole("button", { name: /^データ$|^Data$/i });
    await humanClick(page, dataMenu, 400);
    const genItem = page.getByRole("menuitem", {
      name: /データ生成|Data Generation/i,
    });
    await genItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, genItem, 1000);

    await page
      .getByRole("heading", { name: /新しいデータテーブルを作成|Create.*Table/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-C: データ名・行数を入力 ──────────────────────────────────────
    rec.addCue(
      "データ名と行数を入力します",
      "Enter the table name and row count",
    );
    const nameInput = page.getByLabel(/データ名/i).first();
    await nameInput.clear();
    await nameInput.fill(TABLE_NAME);
    await page.waitForTimeout(300);

    const rowInput = page.getByLabel(/行数/i).first();
    await rowInput.clear();
    await rowInput.fill(ROW_COUNT);
    await page.waitForTimeout(300);

    // ── step-D: 列設定ダイアログを開く ────────────────────────────────────
    rec.addCue(
      "「編集」ボタンで列の分布を設定します",
      "Click 'Edit' to configure the column distribution",
    );
    const editBtn = page.getByRole("button", { name: /^編集$|^Edit$/i }).first();
    await editBtn.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, editBtn, 500);

    const colDialog = page.getByRole("dialog");
    await colDialog.waitFor({ state: "visible", timeout: 10_000 });

    // 列名を設定
    const colNameInput = colDialog.getByRole("textbox").first();
    await colNameInput.clear();
    await colNameInput.fill(COL_NAME);
    await page.waitForTimeout(200);

    // 正規分布を選択
    rec.addCue(
      "分布に「正規分布」を選択します",
      "Select 'Normal distribution' for the column",
    );
    const normalRadio = colDialog.getByRole("radio", {
      name: /^正規分布$|^Normal$/i,
    });
    await normalRadio.waitFor({ state: "visible" });
    await humanClick(page, normalRadio, 400);
    await page.waitForTimeout(400);

    // 設定保存
    const saveBtn = colDialog.getByRole("button", { name: /^設定$|^Save$/i });
    await humanClick(page, saveBtn, 500);
    await colDialog.waitFor({ state: "hidden", timeout: 5_000 });

    // ── step-E: データを作成 ──────────────────────────────────────────────
    rec.addCue(
      "「データを作成」をクリックします",
      "Click 'Create Data' to generate the table",
    );
    const createBtn = page.getByRole("button", {
      name: /データを作成|Create Data/i,
    });
    await humanClick(page, createBtn, 600);

    // テーブルタブが表示されるまで待機
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 30_000 });

    rec.addCue(
      "シミュレーションデータが生成されました",
      "Simulation data has been generated",
    );
    await page.waitForTimeout(2000);

    // 生成されたテーブルをハイライト
    const tableEl = page.getByRole("table").first();
    await highlightElements(page, [tableEl], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-20 収録完了");
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
