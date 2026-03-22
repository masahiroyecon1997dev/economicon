/**
 * E2E ストーリー 03: Excel 取り込み → Join → Union → データ生成 → 計算列
 *
 * ## 使用ファイル
 * - ジョイン1.xlsx（Join 左データ）
 * - ジョイン2.xlsx（Join 右データ）
 * - ユニオン1.csv（Union データ 1）
 * - ユニオン2.csv（Union データ 2）
 *
 * ## 前提
 * - `pnpm tauri:dev:debug` が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルフォルダへのパスがセットされていること
 *
 * ## テストシナリオ概要
 * 1. Excel ファイル 2 件をインポート
 * 2. CSV ファイル 2 件をインポート
 * 3. ヘッダーメニュー → データ → ジョイン を実行
 * 4. ヘッダーメニュー → データ → ユニオン を実行
 * 5. ヘッダーメニュー → データ → データ生成 を実行
 * 6. ヘッダーメニュー → データ → 計算 を実行
 * 7. Excel 形式で保存
 */

import { expect, test } from "@playwright/test";
import {
  clickHeaderMenu,
  closeMessageDialog,
  importFile,
  navigateToSampleDir,
} from "./helpers/appHelpers";
import { setupTauriApp } from "./helpers/setupHelpers";

// ---------------------------------------------------------------------------
// テスト用定数
// ---------------------------------------------------------------------------
const EXCEL_FILE_1 = "ジョイン1.xlsx";
const EXCEL_FILE_2 = "ジョイン2.xlsx";
const CSV_FILE_1 = "ユニオン1.csv";
const CSV_FILE_2 = "ユニオン2.csv";

const JOIN_LEFT_TABLE = "join1";
const JOIN_RIGHT_TABLE = "join2";
const UNION_TABLE_1 = "union1";
const UNION_TABLE_2 = "union2";
const JOINED_TABLE_NAME = "joined_result";
const UNIONED_TABLE_NAME = "unioned_result";
const SIMULATION_TABLE_NAME = "sim_data";

// ---------------------------------------------------------------------------
// テストスイート
// ---------------------------------------------------------------------------
test.describe("03: Excel 取り込み → Join → Union → データ生成 → 計算列", () => {
  // =========================================================================
  // STEP 1: Excel ファイル 2 件をインポート
  // =========================================================================
  test("Step 1: Excel ファイル（ジョイン1・ジョイン2）をインポートする", async ({
    playwright,
  }) => {
    const page = await setupTauriApp(playwright);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();

    await navigateToSampleDir(page);

    // ジョイン1.xlsx をインポート
    await importFile(page, EXCEL_FILE_1, JOIN_LEFT_TABLE);
    await expect(
      page.getByRole("tab", { name: JOIN_LEFT_TABLE }),
    ).toBeVisible();

    // 一度 Import ビューに戻って 2 件目をインポート
    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab2 = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab2.click();
    await navigateToSampleDir(page);

    // ジョイン2.xlsx をインポート
    await importFile(page, EXCEL_FILE_2, JOIN_RIGHT_TABLE);
    await expect(
      page.getByRole("tab", { name: JOIN_RIGHT_TABLE }),
    ).toBeVisible();
  });

  // =========================================================================
  // STEP 2: CSV ファイル 2 件をインポート
  // =========================================================================
  test("Step 2: CSV ファイル（ユニオン1・ユニオン2）をインポートする", async ({
    playwright,
  }) => {
    const page = await setupTauriApp(playwright);
    // ユニオン1.csv をインポート
    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();
    await navigateToSampleDir(page);
    await importFile(page, CSV_FILE_1, UNION_TABLE_1);
    await expect(page.getByRole("tab", { name: UNION_TABLE_1 })).toBeVisible();

    // ユニオン2.csv をインポート
    await clickHeaderMenu(page, /ファイル|File/i, /^取り込み$|^Import$/);
    const fileSelectTab2 = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab2.click();
    await navigateToSampleDir(page);
    await importFile(page, CSV_FILE_2, UNION_TABLE_2);
    await expect(page.getByRole("tab", { name: UNION_TABLE_2 })).toBeVisible();
  });

  // =========================================================================
  // STEP 3: データ → ジョイン
  // =========================================================================
  test("Step 3: データ → ジョインを実行する", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: データ → ジョイン
    await clickHeaderMenu(page, /^データ$|^Data$/i, /ジョイン|Join/i);

    await expect(
      page.getByRole("heading", { name: /データを結合|Join Data/i }),
    ).toBeVisible();

    // ---- 左データを選択 ----
    const leftDataTrigger = page
      .getByLabel(/左データ|Left Data/i)
      .first()
      .or(page.getByRole("combobox").nth(0));
    await leftDataTrigger.click();
    const leftOption = page.getByRole("option", {
      name: JOIN_LEFT_TABLE,
      exact: true,
    });
    await leftOption.waitFor({ state: "visible" });
    await leftOption.click();

    // ---- 右データを選択 ----
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    const rightDataTrigger = page
      .getByLabel(/右データ|Right Data/i)
      .first()
      .or(page.getByRole("combobox").nth(1));
    await rightDataTrigger.click();
    const rightOption = page.getByRole("option", {
      name: JOIN_RIGHT_TABLE,
      exact: true,
    });
    await rightOption.waitFor({ state: "visible" });
    await rightOption.click();

    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 結合キーを設定 ----
    // 自動サジェストが適用されたかチェック
    const autoSuggestMsg = page.getByText(/自動設定しました|Auto-matched/i);
    const hasAutoSuggest = await autoSuggestMsg.isVisible();

    if (!hasAutoSuggest) {
      // 手動でキーペアを設定（左・右それぞれ最初の列を選択）
      const keyPairSection = page
        .locator("div")
        .filter({
          hasText: /結合キー|Key.*Pairs|Join Key/i,
        })
        .last();

      const leftKeyTrigger = keyPairSection.getByRole("combobox").nth(0);
      await leftKeyTrigger.click();
      const leftColOption = page.getByRole("option").first();
      await leftColOption.click();

      const rightKeyTrigger = keyPairSection.getByRole("combobox").nth(1);
      await rightKeyTrigger.click();
      const rightColOption = page.getByRole("option").first();
      await rightColOption.click();
    }

    // ---- 出力データ名を入力 ----
    const newNameInput = page
      .getByLabel(/新しいデータ名|New Data Name/i)
      .first()
      .or(page.getByPlaceholder(/employees_sales_joined/i));
    await newNameInput.fill(JOINED_TABLE_NAME);

    // ---- 結合を実行 ----
    await page.getByRole("button", { name: /結合を実行|Run Join/i }).click();

    // 結果テーブルに遷移してタブが表示されること
    await expect(
      page.getByRole("tab", { name: JOINED_TABLE_NAME }),
    ).toBeVisible({ timeout: 30_000 });
  });

  // =========================================================================
  // STEP 4: データ → ユニオン
  // =========================================================================
  test("Step 4: データ → ユニオンを実行する", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: データ → ユニオン
    await clickHeaderMenu(page, /^データ$|^Data$/i, /ユニオン|Union/i);

    await expect(
      page.getByRole("heading", { name: /データをユニオン|Union Data/i }),
    ).toBeVisible();

    // ---- データを 2 件選択 ----
    // 最初のコンボボックスで 1 件目を選択
    const firstTrigger = page.getByRole("combobox").nth(0);
    await firstTrigger.click();
    const firstOption = page.getByRole("option", {
      name: UNION_TABLE_1,
      exact: true,
    });
    await firstOption.waitFor({ state: "visible" });
    await firstOption.click();

    // 「追加」ボタンで 2 件目を追加
    const addBtn = page.getByRole("button", { name: /^追加$|^Add$/i });
    if (await addBtn.isVisible()) {
      await addBtn.click();
      // 追加された新しいコンボボックスで 2 件目を選択
      const secondTrigger = page.getByRole("combobox").last();
      await secondTrigger.click();
      const secondOption = page.getByRole("option", {
        name: UNION_TABLE_2,
        exact: true,
      });
      await secondOption.waitFor({ state: "visible" });
      await secondOption.click();
    } else {
      // 2 コンボとして並んでいる場合
      const secondTrigger = page.getByRole("combobox").nth(1);
      await secondTrigger.click();
      await page
        .getByRole("option", { name: UNION_TABLE_2, exact: true })
        .click();
    }

    // 共通列がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading column/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 列を「すべて選択」----
    const selectAllBtn = page.getByRole("button", {
      name: /すべて選択|Select all/i,
    });
    if (await selectAllBtn.isVisible()) {
      await selectAllBtn.click();
    } else {
      // 共通列のチェックボックスを個別にチェック（Fallback: ラベルを直接クリック）
      const firstCheckbox = page
        .getByLabel(/対象列|Columns|ユニオンする列/i)
        .first();
      if (await firstCheckbox.isVisible()) {
        await firstCheckbox.check();
      }
    }

    // ---- 出力データ名を入力 ----
    const newNameInput = page
      .getByLabel(/新しいデータ名|New Data Name/i)
      .first()
      .or(page.getByPlaceholder(/sales_union/i));
    await newNameInput.fill(UNIONED_TABLE_NAME);

    // ---- ユニオンを実行 ----
    await page
      .getByRole("button", { name: /ユニオンを実行|Run Union/i })
      .click();

    // 結果タブが表示されること
    await expect(
      page.getByRole("tab", { name: UNIONED_TABLE_NAME }),
    ).toBeVisible({ timeout: 30_000 });
  });

  // =========================================================================
  // STEP 5: データ → データ生成
  // =========================================================================
  test("Step 5: データ生成（シミュレーションデータ作成）", async ({
    playwright,
  }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: データ → データ生成
    await clickHeaderMenu(
      page,
      /^データ$|^Data$/i,
      /データ生成|Data Generation/i,
    );

    await expect(
      page.getByRole("heading", {
        name: /新しいデータテーブルを作成|Create.*Table/i,
      }),
    ).toBeVisible();

    // ---- データ名を入力 ----
    const tableNameInput = page
      .getByLabel(/データ名|Table Name|Data Name/i)
      .first()
      .or(page.getByPlaceholder(/データ名を入力|e\.g\., my_table/i));
    await tableNameInput.fill(SIMULATION_TABLE_NAME);

    // ---- 行数を入力 ----
    const rowCountInput = page
      .getByLabel(/行数|Row Count/i)
      .first()
      .or(page.getByPlaceholder(/1000/i));
    await rowCountInput.fill("100");

    // ---- 列設定: 1 列目の名前と分布を設定 ----
    // 列名入力
    const colNameInput = page
      .getByPlaceholder(/列名を入力|Enter column name/i)
      .first();
    if (await colNameInput.isVisible()) {
      await colNameInput.fill("sim_col_1");
    } else {
      // 列の編集ボタン（鉛筆アイコン）をクリックして列設定ダイアログを開く
      const editBtn = page
        .getByRole("button", { name: /列の編集|Edit Column/i })
        .first();
      if (await editBtn.isVisible()) {
        await editBtn.click();
        const colDialog = page.getByRole("dialog");
        await expect(colDialog).toBeVisible();

        const nameInput = colDialog.getByRole("textbox").first();
        await nameInput.fill("sim_col_1");

        // 分布: 正規分布を選択
        const distTrigger = colDialog.getByRole("combobox").first();
        await distTrigger.click();
        const normalOption = page.getByRole("option", {
          name: /正規分布|Normal/i,
        });
        await normalOption.waitFor({ state: "visible" });
        await normalOption.click();

        await colDialog.getByRole("button", { name: /OK|完了|Done/i }).click();
        await expect(colDialog).toBeHidden();
      }
    }

    // ---- データを作成 ----
    await page
      .getByRole("button", { name: /データを作成|Create Table|Submit/i })
      .click();

    // 作成後にテーブルタブが表示されること
    await expect(
      page.getByRole("tab", { name: SIMULATION_TABLE_NAME }),
    ).toBeVisible({ timeout: 30_000 });
  });

  // =========================================================================
  // STEP 6: データ → 計算列の追加
  // =========================================================================
  test("Step 6: データ → 計算列を追加する", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: データ → 計算
    await clickHeaderMenu(page, /^データ$|^Data$/i, /^計算$|^Calculate$/i);

    await expect(
      page.getByRole("heading", {
        name: /計算式でカラムを追加|Add Column.*Calculation/i,
      }),
    ).toBeVisible();

    // ---- 対象データを選択 ----
    const dataTrigger = page
      .getByLabel(/対象データ|Target Data/i)
      .first()
      .or(page.getByRole("combobox").first());
    await dataTrigger.click();
    // ユニオン1 のデータ（または結合結果）を選択
    const targetOption = page.getByRole("option", {
      name: UNION_TABLE_1,
      exact: true,
    });
    const joinedOption = page.getByRole("option", {
      name: JOINED_TABLE_NAME,
      exact: true,
    });

    if (await targetOption.isVisible()) {
      await targetOption.click();
    } else if (await joinedOption.isVisible()) {
      await joinedOption.click();
    } else {
      // 利用可能な最初のオプションを選択
      await page.getByRole("option").first().click();
    }

    // 列情報がロードされるまで待機
    await expect(
      page.getByText(/列情報を読み込んでいます|Loading/i),
    ).toBeHidden({ timeout: 15_000 });

    // ---- 新しいカラム名を入力 ----
    const newColInput = page
      .getByLabel(/新しいカラム名|New Column Name/i)
      .first()
      .or(page.getByPlaceholder(/total_revenue/i));
    await newColInput.fill("calc_result");

    // ---- 計算式を入力 ----
    // 右側の列一覧から最初の列をクリックして式に挿入 or 直接入力
    const formulaTextarea = page.getByPlaceholder(
      /計算式を入力|Enter your formula/i,
    );
    if (await formulaTextarea.isVisible()) {
      await formulaTextarea.click();
      // 利用可能な列の最初の 2 列を取得して掛け算の式を作る
      const availableCols = page
        .getByRole("listitem")
        .or(
          page
            .getByRole("button")
            .filter({ hasText: /^[a-z_\u3040-\u9fff]+$/i }),
        );

      const firstCol = availableCols.first();
      if (await firstCol.isVisible()) {
        await firstCol.click();
        // 乗算演算子をクリック
        const multiplyBtn = page.getByRole("button", {
          name: /乗算|Multiplication|\*/i,
        });
        if (await multiplyBtn.isVisible()) {
          await multiplyBtn.click();
          await firstCol.click(); // 同じ列で二乗
        }
      } else {
        // 直接入力
        await formulaTextarea.fill("{value} * 2");
      }
    }

    // ---- 計算実行 ----
    await page
      .getByRole("button", { name: /計算を実行|Execute Calculation/i })
      .click();

    // 成功後 DataPreview に遷移して calc_result 列が表示されること
    // または計算成功メッセージが表示されること
    await expect(
      page
        .getByText(/計算が正常に完了|Calculation completed/i)
        .or(
          page.getByRole("columnheader", { name: "calc_result", exact: true }),
        ),
    ).toBeVisible({ timeout: 30_000 });

    await closeMessageDialog(page);
  });

  // =========================================================================
  // STEP 7: Excel 形式で保存
  // =========================================================================
  test("Step 7: Excel 形式で保存する", async ({ playwright }) => {
    const page = await setupTauriApp(playwright);
    // ヘッダーメニュー: ファイル → 保存
    await clickHeaderMenu(page, /ファイル|File/i, /^保存$|^Save$/);

    await expect(
      page.getByRole("heading", { name: /データを保存|Save Data/i }),
    ).toBeVisible();

    // 保存対象データを選択（ジョイン結果を選択）
    const tableNameSelect = page.getByLabel(/保存するデータ|Data to Save/i);
    await tableNameSelect.waitFor({ state: "visible" });
    await tableNameSelect.click();

    // ジョイン結果 or 最初に利用可能なデータを選択
    const joinedOption = page.getByRole("option", {
      name: JOINED_TABLE_NAME,
      exact: true,
    });
    const firstOption = page.getByRole("option").first();

    if (await joinedOption.isVisible()) {
      await joinedOption.click();
    } else {
      await firstOption.click();
    }

    // ファイル名を入力
    const fileNameInput = page.getByLabel(/ファイル名|File Name/i);
    await fileNameInput.fill(`${JOINED_TABLE_NAME}_export`);

    // Excel 形式を選択
    const formatSelect = page.getByLabel(/ファイル形式|File Format/i);
    await formatSelect.click();
    await page
      .getByRole("option", { name: "Excel (.xlsx)", exact: true })
      .click();

    // 保存
    await page.getByRole("button", { name: /^保存$|^Save$/i }).click();

    // 上書き確認があれば OK
    const confirmDlg = page.getByRole("dialog");
    if (await confirmDlg.isVisible()) {
      await confirmDlg.getByRole("button", { name: /OK|はい/i }).click();
    }

    // 成功メッセージを閉じる
    await closeMessageDialog(page);
  });
});
