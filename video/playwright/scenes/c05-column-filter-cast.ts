/**
 * C-05 列フィルタ・型変換 — Playwright 動画収録スクリプト
 *
 * 収録シナリオ:
 *   1. ユニオン1.csv をインポート
 *   2. amount 列 → フィルタ（> 100）→ 新テーブル生成
 *   3. 元テーブルの amount 列 → 型変換（Int64）→ 新列追加
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c05
 *
 * 出力:
 *   captured/c05/frames/0001.jpg … NNNN.jpg
 *   captured/c05/meta.json
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

const SCENE_ID = "c05";
const CSV_FILE_NAME = "ユニオン1.csv";
const TABLE_NAME = "union1";
const TARGET_COL = "amount";
const FILTER_VALUE = "100";
const FILTERED_TABLE_NAME = "union1_filtered";

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

/** 列ヘッダーにホバーして列操作メニューを開く */
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
    await maskDirUsername(page);

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
      `「${TABLE_NAME}」テーブルの列操作メニューを使います`,
      `We'll use the column menu on the '${TABLE_NAME}' table`,
    );
    await page.waitForTimeout(1500);

    // ── step-B: フィルタ操作 ──────────────────────────────────────────────
    rec.addCue(
      `「${TARGET_COL}」列を右クリックしてフィルタを選択します`,
      `Right-click on '${TARGET_COL}' column and select Filter`,
    );
    await openColumnMenu(page, TARGET_COL);

    const filterItem = page.getByRole("menuitem", {
      name: /^フィルタ$|^Filter$/i,
    });
    await filterItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, filterItem, 800);

    // フィルタダイアログ
    const filterDialog = page.getByRole("dialog");
    await filterDialog.waitFor({ state: "visible", timeout: 10_000 });

    rec.addCue(
      `「> ${FILTER_VALUE}」の条件でフィルタします`,
      `Filter rows where the value is greater than ${FILTER_VALUE}`,
    );

    // 演算子を「> より大きい」に設定
    const operatorTrigger = filterDialog.getByRole("combobox").first();
    await operatorTrigger.click();
    const gtOption = page.getByRole("option", {
      name: /> より大きい|> greater/i,
    });
    await gtOption.waitFor({ state: "visible" });
    await humanClick(page, gtOption, 300);

    // 比較値を入力
    const compareInput = filterDialog
      .getByPlaceholder(/比較値|Compare value/i)
      .or(filterDialog.getByRole("textbox").last());
    await compareInput.fill(FILTER_VALUE);
    await page.waitForTimeout(300);

    // 新しいデータ名を入力
    const newNameInput = filterDialog.getByRole("textbox").first();
    if (await newNameInput.isVisible()) {
      const currentVal = await newNameInput.inputValue();
      if (!currentVal) {
        await newNameInput.fill(FILTERED_TABLE_NAME);
      }
    }
    await page.waitForTimeout(500);

    // 適用
    rec.addCue("「フィルタを適用」をクリックします", "Click 'Apply Filter'");
    await filterDialog
      .getByRole("button", { name: /フィルタを適用|Apply Filter/i })
      .click();
    await filterDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // フィルタ結果テーブルを確認
    const filteredTable = page.getByRole("table").first();
    await filteredTable.waitFor({ state: "visible", timeout: 20_000 });

    rec.addCue(
      `「${FILTER_VALUE}」を超える行のみが表示されました`,
      `Only rows with values greater than ${FILTER_VALUE} are shown`,
    );
    await page.waitForTimeout(1500);
    await highlightElements(page, [filteredTable], 2000);

    // ── step-C: 元テーブルに戻る ──────────────────────────────────────────
    const originalTab = page.getByRole("button", { name: TABLE_NAME });
    if (await originalTab.isVisible()) {
      await humanClick(page, originalTab, 500);
    }

    // ── step-D: 型変換 ────────────────────────────────────────────────────
    rec.addCue(
      `次に「${TARGET_COL}」列を型変換します`,
      `Next, let's cast the '${TARGET_COL}' column to a new type`,
    );
    await page.waitForTimeout(800);

    await openColumnMenu(page, TARGET_COL);

    const castItem = page.getByRole("menuitem", { name: /^型変換$|^Cast$/i });
    await castItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, castItem, 800);

    // 型変換ダイアログ
    const castDialog = page.getByRole("dialog");
    await castDialog.waitFor({ state: "visible", timeout: 10_000 });

    rec.addCue(
      "変換先の型を「Int64（整数）」に選択します",
      "Select 'Int64 (integer)' as the target type",
    );

    const typeTrigger = castDialog.getByRole("combobox").first();
    await typeTrigger.click();
    const int64Option = page
      .getByRole("option", { name: /Int64|整数/i })
      .first();
    await int64Option.waitFor({ state: "visible" });
    await humanClick(page, int64Option, 400);
    await page.waitForTimeout(500);

    rec.addCue(
      "「変換」をクリックして新しい列を追加します",
      "Click 'Cast' to add the new column",
    );
    await castDialog.getByRole("button", { name: /^変換$|^Cast$/i }).click();
    await castDialog.waitFor({ state: "hidden", timeout: 30_000 });

    // 変換後の列が追加されたことを確認
    const resultHeader = page
      .getByRole("columnheader", {
        name: new RegExp(`${TARGET_COL}.*cast`, "i"),
      })
      .first();
    await resultHeader.waitFor({ state: "visible", timeout: 15_000 });

    rec.addCue(
      "整数型に変換された新しい列が追加されました",
      "A new column with integer type has been added",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultHeader], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-05 収録完了");
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
