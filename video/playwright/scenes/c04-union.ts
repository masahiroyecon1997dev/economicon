/**
 * C-04 テーブルの Union（縦結合） — Playwright 動画収録スクリプト
 *
 * 録画前に 2 つの CSV テーブルをインポートしておき、
 * 録画中は「データ → ユニオン」の操作フローを見せる。
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c04
 *
 * 出力:
 *   captured/c04/frames/0001.jpg … NNNN.jpg
 *   captured/c04/meta.json
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

const SCENE_ID = "c04";
const CSV_FILE_1 = "ユニオン1.csv";
const CSV_FILE_2 = "ユニオン2.csv";
/** 録画前インポートで使う明示的なテーブル名 */
const TABLE_1 = "union1";
const TABLE_2 = "union2";

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

async function goToImportScreen(page: AppPage): Promise<void> {
  const fileMenuBtn = page.getByRole("banner").getByRole("button", {
    name: /ファイル|File/i,
  });
  await fileMenuBtn.click();

  const importMenuItem = page.getByRole("menuitem", {
    name: /^取り込み$|^Import$/i,
  });
  await importMenuItem.waitFor({ state: "visible", timeout: 5_000 });
  await importMenuItem.click();

  await page
    .getByRole("heading", { name: /ファイルをインポート|Select File/i })
    .waitFor({ state: "visible", timeout: 15_000 });
}

async function preImport(
  page: AppPage,
  fileName: string,
  tableName: string,
): Promise<void> {
  const fileRow = page.getByRole("row", { name: fileName });
  await fileRow.waitFor({ state: "visible", timeout: 15_000 });
  await fileRow.click();

  const dialog = page.getByRole("dialog");
  await dialog.waitFor({ state: "visible", timeout: 10_000 });

  const nameInput = dialog.getByRole("textbox").first();
  await nameInput.fill(tableName);

  const importBtn = dialog.getByRole("button", {
    name: /^インポート$|^Import$/,
  });
  await importBtn.click();
  await dialog.waitFor({ state: "hidden", timeout: 30_000 });

  await page
    .getByRole("button", { name: tableName })
    .waitFor({ state: "visible", timeout: 15_000 });
}

// ---------------------------------------------------------------------------
// メイン
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const { browser, context, page } = await connectToApp();

  try {
    // ── ① 録画前: ワークスペースリセット ─────────────────────────────────
    await resetWorkspace(page);

    // ── ② 録画前: 2 つの CSV ファイルをインポート ─────────────────────────
    console.log("  ⏳ union1 / union2 をインポート中（録画前）...");
    await navigateToSampleDir(page);
    await preImport(page, CSV_FILE_1, TABLE_1);
    console.log(`     ✅ ${TABLE_1} インポート完了`);

    await goToImportScreen(page);
    await navigateToSampleDir(page);
    await preImport(page, CSV_FILE_2, TABLE_2);
    console.log(`     ✅ ${TABLE_2} インポート完了`);
    await page.waitForTimeout(500);

    // ── ③ 録画開始 ────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: 2 つのテーブルを確認 ─────────────────────────────────────
    rec.addCue(
      "2 つの CSV テーブルが取り込まれています",
      "Two CSV tables have been imported",
    );
    await page.waitForTimeout(1500);

    // ── ④ データ → ユニオンへ遷移 ─────────────────────────────────────────
    rec.addCue(
      "「データ」→「ユニオン」を選択します",
      "Select 'Data' → 'Union'",
    );

    const dataMenuBtn = page.getByRole("banner").getByRole("button", {
      name: /^データ$|^Data$/i,
    });
    await humanClick(page, dataMenuBtn, 400);

    const unionItem = page.getByRole("menuitem", {
      name: /ユニオン|Union/i,
    });
    await unionItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, unionItem, 1000);

    await page
      .getByRole("heading", { name: /データをユニオン|Union Data/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-B: 1 つ目のテーブルを選択 ───────────────────────────────────
    rec.addCue(
      `1 つ目のテーブル「${TABLE_1}」を選択して追加します`,
      `Select '${TABLE_1}' and add it`,
    );

    const firstTrigger = page.getByRole("combobox").nth(0);
    await humanClick(page, firstTrigger, 400);

    const firstOption = page.getByRole("option", {
      name: TABLE_1,
      exact: true,
    });
    await firstOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, firstOption, 400);

    const addBtn = page.getByRole("button", { name: /^追加$|^Add$/i });
    await humanClick(page, addBtn, 800);

    // ── step-C: 2 つ目のテーブルを選択 ───────────────────────────────────
    rec.addCue(
      `2 つ目のテーブル「${TABLE_2}」を選択して追加します`,
      `Select '${TABLE_2}' and add it`,
    );

    const secondTrigger = page.getByRole("combobox").last();
    await humanClick(page, secondTrigger, 400);

    const secondOption = page.getByRole("option", {
      name: TABLE_2,
      exact: true,
    });
    await secondOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, secondOption, 400);
    await humanClick(page, addBtn, 800);

    // 列情報ロード待機
    await page
      .getByText(/列情報を読み込んでいます|Loading column/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // ── step-D: すべての列を選択 ─────────────────────────────────────────
    rec.addCue(
      "結合に含める列を「すべて選択」します",
      "Click 'Select all' to include all columns",
    );

    const selectAllBtn = page.getByRole("button", {
      name: /すべて選択|Select all/i,
    });
    if (await selectAllBtn.isVisible()) {
      await humanClick(page, selectAllBtn, 600);
    } else {
      // フォールバック: 最初のチェックボックスをチェック
      const firstCheckbox = page.getByRole("checkbox").first();
      if (await firstCheckbox.isVisible()) {
        await humanClick(page, firstCheckbox, 400);
      }
    }
    await page.waitForTimeout(500);

    // ── ⑤ ユニオンを実行 ─────────────────────────────────────────────────
    rec.addCue("「ユニオンを実行」をクリックします", "Click 'Run Union'");

    const runUnionBtn = page.getByRole("button", {
      name: /ユニオンを実行|Run Union/i,
    });
    await humanClick(page, runUnionBtn, 500);

    // 結果テーブルが表示されるまで待機
    const resultTable = page.getByRole("table").first();
    await resultTable.waitFor({ state: "visible", timeout: 30_000 });

    // ── step-E: 結果を確認 ────────────────────────────────────────────────
    rec.addCue(
      "2 つのテーブルが縦方向に結合されました",
      "The two tables have been stacked vertically",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultTable], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-04 収録完了");
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
