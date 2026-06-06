/**
 * C-03 テーブルの Join（結合） — Playwright 動画収録スクリプト
 *
 * 録画前に 2 つの Excel テーブルをインポートしておき、
 * 録画中は「データ → ジョイン」の操作フローを見せる。
 *
 * 実行前提:
 *   - VS Code タスク「Economicon: App (Debug Port)」でアプリが起動済みであること
 *   - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダパスを設定（省略時は ../../../sample）
 *
 * 実行方法:
 *   cd video/playwright
 *   pnpm capture:c03
 *
 * 出力:
 *   captured/c03/frames/0001.jpg … NNNN.jpg
 *   captured/c03/meta.json
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

const SCENE_ID = "c03";
const EXCEL_FILE_1 = "ジョイン1.xlsx";
const EXCEL_FILE_2 = "ジョイン2.xlsx";
/** 録画前インポートで使う明示的なテーブル名 */
const TABLE_LEFT = "join1";
const TABLE_RIGHT = "join2";

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

/** 録画前インポート（ヘッダーメニュー経由でインポート画面へ） */
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

/** ファイルをクリックしてテーブル名を指定してインポート（録画前用・高速） */
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
    await maskDirUsername(page);

    // ── ② 録画前: 2 つの Excel ファイルをインポート ───────────────────────
    console.log("  ⏳ join1 / join2 をインポート中（録画前）...");
    await navigateToSampleDir(page);
    await preImport(page, EXCEL_FILE_1, TABLE_LEFT);
    console.log(`     ✅ ${TABLE_LEFT} インポート完了`);

    await goToImportScreen(page);
    await navigateToSampleDir(page);
    await preImport(page, EXCEL_FILE_2, TABLE_RIGHT);
    console.log(`     ✅ ${TABLE_RIGHT} インポート完了`);
    await page.waitForTimeout(500);

    // ── ③ 録画開始 ────────────────────────────────────────────────────────
    const rec = await Recorder.create(context, page, SCENE_ID);
    await rec.start();
    console.log("  ▶ 録画開始");

    // ── step-A: 2 つのテーブルを確認 ─────────────────────────────────────
    rec.addCue(
      "2 つの Excel テーブルが取り込まれています",
      "Two Excel tables have been imported",
    );
    await page.waitForTimeout(1500);

    // ── ④ データ → ジョインへ遷移 ─────────────────────────────────────────
    rec.addCue("「データ」→「ジョイン」を選択します", "Select 'Data' → 'Join'");

    const dataMenuBtn = page.getByRole("banner").getByRole("button", {
      name: /^データ$|^Data$/i,
    });
    await humanClick(page, dataMenuBtn, 400);

    const joinItem = page.getByRole("menuitem", {
      name: /ジョイン|Join/i,
    });
    await joinItem.waitFor({ state: "visible", timeout: 5_000 });
    await humanClick(page, joinItem, 1000);

    await page
      .getByRole("heading", { name: /データを結合|Join Data/i })
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── step-B: 左データを選択 ─────────────────────────────────────────────
    rec.addCue(
      `左データに「${TABLE_LEFT}」を選択します`,
      `Select '${TABLE_LEFT}' as the left data`,
    );

    const leftDataTrigger = page
      .getByLabel(/左データ|Left Data/i)
      .first()
      .or(page.getByRole("combobox").nth(0));
    await humanClick(page, leftDataTrigger, 400);

    const leftOption = page.getByRole("option", {
      name: TABLE_LEFT,
      exact: true,
    });
    await leftOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, leftOption, 800);

    await page
      .getByText(/列情報を読み込んでいます|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // ── step-C: 右データを選択 ─────────────────────────────────────────────
    rec.addCue(
      `右データに「${TABLE_RIGHT}」を選択します`,
      `Select '${TABLE_RIGHT}' as the right data`,
    );

    const rightDataTrigger = page
      .getByLabel(/右データ|Right Data/i)
      .first()
      .or(page.getByRole("combobox").nth(1));
    await humanClick(page, rightDataTrigger, 400);

    const rightOption = page.getByRole("option", {
      name: TABLE_RIGHT,
      exact: true,
    });
    await rightOption.waitFor({ state: "visible", timeout: 10_000 });
    await humanClick(page, rightOption, 800);

    await page
      .getByText(/列情報を読み込んでいます|Loading/i)
      .waitFor({ state: "hidden", timeout: 15_000 })
      .catch(() => {});

    // ── step-D: 結合キーを確認 ────────────────────────────────────────────
    // 自動サジェストが適用された場合は字幕でそれを説明
    const autoSuggestMsg = page.getByText(/自動設定しました|Auto-matched/i);
    const hasAutoSuggest = await autoSuggestMsg.isVisible().catch(() => false);

    if (hasAutoSuggest) {
      rec.addCue(
        "共通キー列が自動で設定されました",
        "A common key column was automatically detected",
      );
    } else {
      rec.addCue(
        "結合に使うキー列を設定します",
        "Set the key column for joining",
      );
      // キーが自動設定されない場合は最初の列を手動選択
      const keyPairSection = page
        .locator("div")
        .filter({ hasText: /結合キー|Key.*Pairs|Join Key/i })
        .last();
      const leftKeyTrigger = keyPairSection.getByRole("combobox").nth(0);
      if (await leftKeyTrigger.isVisible()) {
        await humanClick(page, leftKeyTrigger, 300);
        const firstOption = page.getByRole("option").first();
        await firstOption.waitFor({ state: "visible" });
        await humanClick(page, firstOption, 300);

        const rightKeyTrigger = keyPairSection.getByRole("combobox").nth(1);
        if (await rightKeyTrigger.isVisible()) {
          await humanClick(page, rightKeyTrigger, 300);
          const secondOption = page.getByRole("option").first();
          await secondOption.waitFor({ state: "visible" });
          await humanClick(page, secondOption, 300);
        }
      }
    }
    await page.waitForTimeout(800);

    // ── ⑤ 結合を実行 ─────────────────────────────────────────────────────
    rec.addCue("「結合を実行」をクリックします", "Click 'Run Join'");

    const runJoinBtn = page.getByRole("button", {
      name: /結合を実行|Run Join/i,
    });
    await humanClick(page, runJoinBtn, 500);

    // 結果テーブルが表示されるまで待機
    const resultTable = page.getByRole("table").first();
    await resultTable.waitFor({ state: "visible", timeout: 30_000 });

    // ── step-E: 結果を確認 ────────────────────────────────────────────────
    rec.addCue(
      "2 つのテーブルが横方向に結合されました",
      "The two tables have been joined side by side",
    );
    await page.waitForTimeout(2000);
    await highlightElements(page, [resultTable], 2500);

    // ── 録画停止 ──────────────────────────────────────────────────────────
    const info = await rec.stop();
    console.log("");
    console.log("✅ C-03 収録完了");
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
