/**
 * C-06 変換列・ダミー変数の追加 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. ユニオン1.csv をインポート
 *   2. amount 列 → 変換列を追加（対数変換）
 *   3. category 列（文字列列）→ ダミー変数を追加
 *      ※ category 列がなければ amount 列で代替
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c06
 *
 * 出力:
 *   captured/c06/frames/0001.jpg … NNNN.jpg
 *   captured/c06/meta.json
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

const SCENE_ID = "c06";
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1";
const NUMERIC_COL = "amount";
/** ダミー変数化する列。category が存在すればそちらを使う */
const DUMMY_COL_CANDIDATE = "category";

// ---------------------------------------------------------------------------
// ヘルパー
// ---------------------------------------------------------------------------

type AppPage = Awaited<ReturnType<typeof connectToApp>>["page"];

async function navigateToSampleDir(page: AppPage): Promise<void> {
  const fileSelectTab = page.getByRole("tab", {
    name: /ファイル選択|Select File/i,
  });
  if (await fileSelectTab.isVisible()) {
    await fileSelectTab.click();
  }
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
    const confirmDialog = page
      .getByRole("dialog")
      .or(page.getByRole("alertdialog"));
    await confirmDialog.waitFor({ state: "visible", timeout: 10_000 });
    await confirmDialog.getByRole("button", { name: /^OK$/i }).click();
    await confirmDialog.waitFor({ state: "hidden", timeout: 10_000 });
  }
  await page
    .getByRole("heading", { name: /ファイルをインポート|Select File/i })
    .waitFor({ state: "visible", timeout: 30_000 });
}

async function openColumnMenu(
  page: AppPage,
  columnName: string,
): Promise<void> {
  const header = page.getByRole("columnheader", { name: columnName }).first();
  await header.hover();
  const menuBtn = header.getByRole("button", {
    name: /列操作|Column operations/i,
  });
  await menuBtn.waitFor({ state: "visible", timeout: 5_000 });
  await menuBtn.click();
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // ── 録画前準備 ────────────────────────────────────────────────────────
    await resetWorkspace(page);
    await navigateToSampleDir(page);

    // CSV インポート（録画前）
    const fileRow = page.getByRole("row", { name: CSV_FILE_NAME });
    await fileRow.waitFor({ state: "visible", timeout: 15_000 });
    await fileRow.click();

    const importDialog = page.getByRole("dialog");
    await importDialog.waitFor({ state: "visible", timeout: 10_000 });
    const nameInput = importDialog.getByRole("textbox").first();
    await nameInput.fill(TABLE_NAME);
    await importDialog
      .getByRole("button", { name: /^インポート$|^Import$/ })
      .click();
    await importDialog.waitFor({ state: "hidden", timeout: 30_000 });
    await page
      .getByRole("button", { name: TABLE_NAME })
      .waitFor({ state: "visible", timeout: 15_000 });
    await page.waitForTimeout(500);

    // ── 録画開始 ────────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: テーブルを確認 ────────────────────────────────────────────
    rec.addCue(
      "列メニューから変換列とダミー変数を追加できます",
      "We can add transform columns and dummy variables from the column menu",
    );
    await page.waitForTimeout(1500);

    // ====================================================================
    // PART 1: 変換列を追加（対数変換）
    // ====================================================================

    rec.addCue(
      `「${NUMERIC_COL}」列に対数変換列を追加します`,
      `Adding a logarithm transform column to '${NUMERIC_COL}'`,
    );
    await openColumnMenu(page, NUMERIC_COL);

    const transformItem = page.getByRole("menuitem", {
      name: /変換列を追加|Add Transform Column/i,
    });
    await transformItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, transformItem, 800);

    const transformDialog = page.getByRole("dialog");
    await transformDialog.waitFor({ state: "visible", timeout: 10_000 });

    // 変換方法: 対数変換を選択
    const methodTrigger = transformDialog.getByRole("combobox").first();
    await methodTrigger.click();
    const logOption = page.getByRole("option", {
      name: /対数変換|Logarithm/i,
    });
    await logOption.waitFor({ state: "visible" });
    await humanClick(page, logOption, 400);
    await page.waitForTimeout(500);

    rec.addCue(
      "「追加」をクリックして対数変換列を生成します",
      "Click 'Add' to create the log-transformed column",
    );
    await transformDialog
      .getByRole("button", { name: /^追加$|^Add$/i })
      .click();
    await transformDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // 追加後の確認
    const transformedTable = page.getByRole("table").first();
    await transformedTable.waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      "対数変換された新しい列が追加されました",
      "A new log-transformed column has been added",
    );
    await page.waitForTimeout(1500);
    await highlightElements(page, [transformedTable], 2000);

    // ====================================================================
    // PART 2: ダミー変数を追加
    // ====================================================================

    // ダミー変数化する列を決定（category または NUMERIC_COL）
    const hasCategoryCol = await page
      .getByRole("columnheader", { name: DUMMY_COL_CANDIDATE })
      .isVisible();
    const dummyCol = hasCategoryCol ? DUMMY_COL_CANDIDATE : NUMERIC_COL;

    rec.addCue(
      `「${dummyCol}」列にダミー変数を追加します`,
      `Adding a dummy variable column to '${dummyCol}'`,
    );
    await openColumnMenu(page, dummyCol);

    const dummyItem = page.getByRole("menuitem", {
      name: /ダミー変数を追加|Add Dummy Column/i,
    });
    await dummyItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, dummyItem, 800);

    const dummyDialog = page.getByRole("dialog");
    await dummyDialog.waitFor({ state: "visible", timeout: 10_000 });

    // ターゲット値を入力（シングルモード）
    rec.addCue(
      "ダミー化する値を入力します",
      "Enter the target value to dummy-encode",
    );
    const targetInput = dummyDialog
      .getByPlaceholder(/例: Tokyo|例:/i)
      .or(dummyDialog.getByRole("textbox").first());
    await targetInput.fill(hasCategoryCol ? "A" : "1");
    await page.waitForTimeout(500);

    rec.addCue(
      "「追加」をクリックしてダミー変数列を生成します",
      "Click 'Add' to create the dummy column",
    );
    await dummyDialog.getByRole("button", { name: /^追加$|^Add$/i }).click();
    await dummyDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // 追加後の確認
    const afterDummyTable = page.getByRole("table").first();
    await afterDummyTable.waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      "0/1 のダミー変数列が追加されました",
      "A binary dummy variable column (0/1) has been added",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [afterDummyTable], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-06 収録完了");
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
