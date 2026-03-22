/**
 * E2E テスト共通ヘルパー
 *
 * ## 前提
 * - アプリのデフォルト言語は日本語（ja）
 * - Tauri サイドカー（Python FastAPI）が起動済みであること
 * - 環境変数 ECONOMICON_TEST_SAMPLE_DIR にサンプルファイルのフォルダパスをセットすること
 *   例: C:\Users\masak\Desktop\repos\economicon\sample
 */

import type { Locator, Page } from "@playwright/test";
import { expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
// ---------------------------------------------------------------------------
// 定数
// ---------------------------------------------------------------------------

/**
 * サンプルデータフォルダのパス。
 * 環境変数 ECONOMICON_TEST_SAMPLE_DIR が設定されていない場合はデフォルト値を使用。
 */
// 現在のファイルの絶対パスを取得

const __filename = fileURLToPath(import.meta.url);
// 現在のディレクトリパスを取得
const __dirname = path.dirname(__filename);
export const SAMPLE_DIR =
  process.env.ECONOMICON_TEST_SAMPLE_DIR ??
  path.resolve(__dirname, "../../sample");

/** ローディングオーバーレイが消えるまでの最大待機時間 (ms) */
const LOADING_TIMEOUT_MS = 90_000;

/** API 応答待機の標準タイムアウト (ms) */
const API_TIMEOUT_MS = 30_000;

// ---------------------------------------------------------------------------
// アプリ起動待機
// ---------------------------------------------------------------------------

/**
 * Tauri サイドカー（Python FastAPI）の起動を含むアプリ初期化完了を待機する。
 *
 * チェック条件:
 * 1. ローディングオーバーレイが消えること
 * 2. ファイル一覧テーブルが表示されること（ImportDataFile ビューへの遷移）
 */
export async function waitForAppReady(page: Page): Promise<void> {
  await page.goto("/");

  // ローディングオーバーレイが消えるまで待機（サイドカー起動に最大 90 秒）
  // オーバーレイは role="status" または "処理中"/"起動中" テキストを含む
  await expect(
    page.getByRole("status").or(page.getByText(/起動中|処理中|Loading/i)),
  )
    .toBeHidden({ timeout: LOADING_TIMEOUT_MS })
    .catch(() => {
      // ローディングが一瞬で終わっている場合は無視
    });

  // ImportDataFile ビューのタイトルが表示されるまで待機
  await expect(
    page.getByRole("heading", { name: /ファイルをインポート|Select File/i }),
  ).toBeVisible({ timeout: LOADING_TIMEOUT_MS });
}

// ---------------------------------------------------------------------------
// ファイルブラウザ操作
// ---------------------------------------------------------------------------

/**
 * ImportDataFile ビューまたは SaveData ビューのファイルブラウザで
 * 指定したディレクトリに移動する。
 *
 * ブレッドクラムで移動できない場合は、上位ディレクトリボタンを繰り返し押す代わりに
 * 検索フィールドの上にある直接パス操作を実施。
 *
 * 実装方針: SAMPLE_DIR のパスセグメントを上位から辿り、
 * 現在のパンくずに含まれていない部分をフォルダクリックで降りていく。
 */
export async function navigateToSampleDir(page: Page): Promise<void> {
  // "ファイル選択" タブに切り替え
  const fileSelectTab = page.getByRole("tab", {
    name: /ファイル選択|Select File/i,
  });
  if (await fileSelectTab.isVisible()) {
    await fileSelectTab.click();
  }

  // サンプルディレクトリのパスをセグメントに分割
  // Windows: "C:\Users\..." → ["C:", "Users", ...]
  // Unix:    "/home/..." → ["home", ...]
  const sep: string = path.sep;
  console.log(`SAMPLE_DIR: ${SAMPLE_DIR}, sep: ${sep}`);
  const segments = SAMPLE_DIR.split(sep).filter((s: string) => s.length > 0);

  // ブレッドクラム取得（現在のパスを読み取る）
  // パスが既に正しければ何もしない
  for (const segment of segments) {
    const searchInput = page
      .getByPlaceholder(/ファイル名で検索|Search by file name/i)
      .first();
    await searchInput.waitFor({ state: "visible", timeout: API_TIMEOUT_MS });

    // フォルダ行をクリックして降りる
    // 既にそのフォルダ内にいる場合はスキップ
    const folderRow = page
      .getByRole("row", { name: segment })
      .filter({ hasNot: page.locator('[data-file="true"]') });

    if (await folderRow.isVisible()) {
      await folderRow.click();
      await page.waitForLoadState("domcontentloaded");
    }
  }
}

// ---------------------------------------------------------------------------
// ファイルインポート
// ---------------------------------------------------------------------------

/**
 * 指定したファイル名の行をクリックしてインポートダイアログを開き、
 * インポートを実行するまでの一連の操作を行う。
 *
 * @param page - Playwright Page
 * @param fileName - ファイル名（例: "ユニオン1.csv"）
 * @param tableName - インポート後のデータ名（省略時はファイル名ベース）
 */
export async function importFile(
  page: Page,
  fileName: string,
  tableName?: string,
): Promise<void> {
  // ファイル行を見つけてクリック → ImportConfigDialog が開く
  const fileRow = page.getByRole("row", { name: fileName });
  await expect(fileRow).toBeVisible({ timeout: API_TIMEOUT_MS });
  await fileRow.click();

  // インポート設定ダイアログが開くのを待機
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: API_TIMEOUT_MS });

  // データ名の上書きが指定されている場合
  if (tableName) {
    const nameInput = dialog.getByRole("textbox").first();
    await nameInput.fill(tableName);
  }

  // 「インポート」ボタンをクリック
  const importBtn = dialog.getByRole("button", {
    name: /^インポート$|^Import$/,
  });
  await importBtn.click();

  // ダイアログが閉じ、DataPreview ビューに遷移するまで待機
  await expect(dialog).toBeHidden({ timeout: API_TIMEOUT_MS });
}

// ---------------------------------------------------------------------------
// ヘッダーメニュー操作
// ---------------------------------------------------------------------------

/**
 * ヘッダーメニューを開いてメニューアイテムをクリックする。
 *
 * @param page - Playwright Page
 * @param menuName - メニュー名テキスト（例: "データ"）
 * @param itemName - サブメニューアイテム名テキスト（例: "ジョイン"）
 */
export async function clickHeaderMenu(
  page: Page,
  menuName: string | RegExp,
  itemName: string | RegExp,
): Promise<void> {
  // メニューボタンをクリック（header 内の nav ボタン）
  const menuBtn = page.getByRole("banner").getByRole("button", {
    name: menuName,
  });
  await menuBtn.click();

  // サブメニューアイテムをクリック
  const item = page.getByRole("menuitem", { name: itemName });
  await item.click();
}

// ---------------------------------------------------------------------------
// 列コンテキストメニュー
// ---------------------------------------------------------------------------

/**
 * テーブルの列ヘッダーをホバーして列操作メニューを開く。
 *
 * ColumnContextMenu は opacity-0 -> opacity-100 の CSS トランジションで
 * 表示されるため、hover() の後に waitFor を挟む必要がある。
 *
 * @param page - Playwright Page
 * @param columnName - 列名テキスト（完全一致）
 * @returns DropdownMenu.Content ロケータ
 */
export async function openColumnMenu(
  page: Page,
  columnName: string,
): Promise<void> {
  const header = page.getByRole("columnheader", { name: columnName }).first();
  await expect(header).toBeVisible({ timeout: API_TIMEOUT_MS });
  await header.hover();

  // opacity-0 ボタンが表示されるまで待機
  const menuBtn = header.getByRole("button", {
    name: /列操作|Column operations/i,
  });
  await menuBtn.waitFor({ state: "visible", timeout: 5000 });
  await menuBtn.click();
}

/**
 * 列メニューアイテムをクリックする。
 * openColumnMenu() を事前に呼び出しておくこと。
 *
 * @param page - Playwright Page
 * @param itemName - メニューアイテム名の正規表現または文字列
 */
export async function clickColumnMenuItem(
  page: Page,
  itemName: string | RegExp,
): Promise<void> {
  const item = page.getByRole("menuitem", { name: itemName });
  await item.waitFor({ state: "visible", timeout: API_TIMEOUT_MS });
  await item.click();
}

// ---------------------------------------------------------------------------
// 左サイドバー データメニュー
// ---------------------------------------------------------------------------

/**
 * 左サイドバーの指定データのコンテキストメニューを開く。
 *
 * TableNavItem の MoreVertical ボタンは opacity-0 なので hover() が必要。
 *
 * @param page - Playwright Page
 * @param tableName - データ名
 */
export async function openTableContextMenu(
  page: Page,
  tableName: string,
): Promise<void> {
  // サイドバー内のテーブル名 span を hover
  const tableItem = page
    .getByRole("navigation")
    .locator(`span[title="${tableName}"]`)
    .filter({ hasText: tableName })
    .first();
  await expect(tableItem).toBeVisible({ timeout: API_TIMEOUT_MS });
  await tableItem.hover();

  // MoreVertical ボタンが現れるまで待機してクリック
  const moreBtn = page
    .getByRole("navigation")
    .locator(`span:has-text("${tableName}")`)
    .locator("xpath=..")
    .getByRole("button", { name: /データメニュー|DataMenu/i });

  // aria-label は AreaLabels.DataMenu キーによる翻訳テキスト
  // 念のため parent の sibling button も探す
  const moreBtnFallback = page
    .getByRole("navigation")
    .filter({ hasText: tableName })
    .locator("button")
    .last();

  const btn = (await moreBtn.isVisible()) ? moreBtn : moreBtnFallback;
  await btn.waitFor({ state: "visible", timeout: 5000 });
  await btn.click();
}

/**
 * 左サイドバーのテーブル名をクリックしてデータプレビューを開く。
 */
export async function clickTableInSidebar(
  page: Page,
  tableName: string,
): Promise<void> {
  const span = page
    .getByRole("navigation")
    .getByText(tableName, { exact: true })
    .first();
  await expect(span).toBeVisible({ timeout: API_TIMEOUT_MS });
  await span.click();

  // DataPreview（テーブルタブ）が表示されるまで待機
  await expect(page.getByRole("tab", { name: tableName })).toBeVisible({
    timeout: API_TIMEOUT_MS,
  });
}

// ---------------------------------------------------------------------------
// ダイアログ操作ヘルパー
// ---------------------------------------------------------------------------

/**
 * 現在開いているダイアログのテキストボックスに値を入力して Submit ボタンを押す。
 *
 * @param page - Playwright Page
 * @param value - 入力する値
 * @param submitLabel - Submit ボタンのラベル（正規表現 or 文字列）
 */
export async function fillDialogAndSubmit(
  page: Page,
  value: string,
  submitLabel: string | RegExp,
): Promise<void> {
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: API_TIMEOUT_MS });

  const input = dialog.getByRole("textbox");
  await input.fill(value);

  const submitBtn = dialog.getByRole("button", { name: submitLabel });
  await submitBtn.click();

  await expect(dialog).toBeHidden({ timeout: API_TIMEOUT_MS });
}

// ---------------------------------------------------------------------------
// コンファームダイアログ
// ---------------------------------------------------------------------------

/**
 * OK/確認/Delete などのコンファームダイアログのボタンをクリックする。
 */
export async function confirmDialog(
  page: Page,
  buttonLabel: string | RegExp = /^OK$|^削除$|^Delete$/i,
): Promise<void> {
  const dialog = page.getByRole("dialog").or(page.getByRole("alertdialog"));
  await expect(dialog).toBeVisible({ timeout: API_TIMEOUT_MS });
  await dialog.getByRole("button", { name: buttonLabel }).click();
  await expect(dialog).toBeHidden({ timeout: API_TIMEOUT_MS });
}

// ---------------------------------------------------------------------------
// MessageDialog（情報メッセージ）を閉じるヘルパー
// ---------------------------------------------------------------------------

/**
 * アプリが表示する MessageDialog（エラー/成功メッセージ）を閉じる。
 * ダイアログが表示されていない場合は何もしない。
 */
export async function closeMessageDialog(page: Page): Promise<void> {
  try {
    const dialog = page.getByRole("dialog");
    if (await dialog.isVisible()) {
      const okBtn = dialog.getByRole("button", { name: /^OK$/i });
      if (await okBtn.isVisible()) {
        await okBtn.click();
        await expect(dialog).toBeHidden({ timeout: 5000 });
      }
    }
  } catch {
    // ダイアログが存在しない場合は無視
  }
}

// ---------------------------------------------------------------------------
// Select コンポーネントのヘルパー
// ---------------------------------------------------------------------------

/**
 * Radix UI Select を操作して指定した値を選択する。
 *
 * @param trigger - Select トリガーのロケータ
 * @param optionName - 選択するオプションのテキスト
 */
export async function selectOption(
  trigger: Locator,
  optionName: string,
): Promise<void> {
  await trigger.click();
  const option = trigger
    .page()
    .getByRole("option", { name: optionName, exact: true });
  await option.waitFor({ state: "visible", timeout: API_TIMEOUT_MS });
  await option.click();
}
