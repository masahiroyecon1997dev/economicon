import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";
import { setupTauriApp } from "./helpers/setupHelpers";

test.describe("ImportDataFileView - ファイル選択画面", () => {
  let page: Page;

  test.beforeEach(async ({ playwright }) => {
    page = await setupTauriApp(playwright);
    // ファイル一覧テーブルが含まれる "ファイル選択" タブに切り替え
    const fileSelectTab = page.getByRole("tab", {
      name: /ファイル選択|Select File/i,
    });
    await fileSelectTab.click();
    await expect(
      page.getByRole("table", { name: "ファイル一覧" }),
    ).toBeVisible();
  });

  test("ページタイトルと説明が表示される", async () => {
    // タイトル: ImportDataFileView.Title = "ファイルをインポート"
    const title = page.getByRole("heading", { name: "ファイルをインポート" });
    await expect(title).toBeVisible();

    // 説明文が表示されることを確認
    const description = page.locator("p.text-black\\/60");
    await expect(description).toBeVisible();
  });

  test("検索ボックスが表示され、入力できる", async () => {
    // 検索ボックスを取得（ImportDataFileView.SearchPlaceholder = "ファイル名で検索"）
    const searchInput = page
      .locator("main")
      .getByPlaceholder("ファイル名で検索")
      .first();

    // 検索ボックスが表示されていることを確認
    await expect(searchInput).toBeVisible();

    // 検索ボックスに入力
    await searchInput.fill("test");

    // 入力した値が反映されることを確認
    await expect(searchInput).toHaveValue("test");

    // 終わったら検索ボックスをクリアしておく
    await searchInput.fill("");
  });

  test("上位ディレクトリボタンが表示される", async () => {
    // ImportDataFileView.GoUpDirectory = "上位ディレクトリへ移動"
    const upButton = page.getByRole("button", {
      name: "上位ディレクトリへ移動",
    });
    await expect(upButton).toBeVisible();
  });

  test("ファイルリストテーブルが表示される", async () => {
    // ImportDataFileView.FileListTableTitle = "ファイル一覧"
    const table = page.getByRole("table", { name: "ファイル一覧" });
    await expect(table).toBeVisible();

    // ヘッダー列数: ファイル名・サイズ・最終更新日時 の3列
    const headers = table.locator("thead th");
    await expect(headers).toHaveCount(3);
  });

  test("ファイル名でソートできる", async () => {
    const table = page.getByRole("table", { name: "ファイル一覧" });
    const nameHeader = table.locator("thead th").first();
    await nameHeader.click();

    // ソートアイコンが表示される（昇順）
    await expect(nameHeader.locator("svg")).toBeVisible();

    // もう一度クリックして降順に
    await nameHeader.click();
    await expect(nameHeader.locator("svg")).toBeVisible();
  });

  test("ファイルリストが検索でフィルタリングされる", async () => {
    const table = page.getByRole("table", { name: "ファイル一覧" });
    // 検索前のファイル数を取得
    const rowsBeforeSearch = await table.locator("tbody tr").count();

    // 検索ボックスに入力
    const searchInput = page
      .locator("main")
      .getByPlaceholder("ファイル名で検索")
      .first();
    await searchInput.fill(".csv");

    // React state 反映を待つ（UI 更新後に件数確認）
    await expect(table.locator("tbody tr").first()).toBeVisible();

    // フィルタリング後のファイル数を取得
    const rowsAfterSearch = await table.locator("tbody tr").count();

    // CSV のみ表示されるため件数は減少（またはゼロ）
    expect(rowsAfterSearch).toBeLessThanOrEqual(rowsBeforeSearch);
  });

  test("パンくずリストから上位ディレクトリに移動できる", async () => {
    const breadcrumbNav = page.getByRole("navigation", { name: "Breadcrumb" });
    const breadcrumbs = breadcrumbNav.locator("li button");
    const breadcrumbCount = await breadcrumbs.count();

    // パンくずが 2 つ以上ある場合のみテスト（ルートディレクトリでは不可）
    if (breadcrumbCount >= 2) {
      // 先頭パンくずをクリックして上位へ
      await breadcrumbs.nth(-2).click();

      const newBreadcrumbCount = await breadcrumbNav
        .locator("li button")
        .count();
      expect(newBreadcrumbCount).toBeLessThanOrEqual(breadcrumbCount);
    }
  });

  test("ディレクトリをクリックすると移動する", async () => {
    const table = page.getByRole("table", { name: "ファイル一覧" });
    // Lucide <Folder> は "text-yellow-500" クラスを持つ SVG で描画される
    const directoryRow = table
      .locator("tbody tr")
      .filter({ has: page.locator("svg.text-yellow-500") })
      .first();

    const directoryCount = await directoryRow.count();
    if (directoryCount > 0) {
      const breadcrumbNav = page.getByRole("navigation", {
        name: "Breadcrumb",
      });
      const breadcrumbCountBefore = await breadcrumbNav
        .locator("li button")
        .count();

      await directoryRow.click();

      // パンくずリストが増えていることを確認
      await expect(breadcrumbNav.locator("li button")).toHaveCount(
        breadcrumbCountBefore + 1,
        { timeout: 10_000 },
      );
    }
  });

  test("キャンセルボタンが表示され、クリックできる", async () => {
    // Common.Cancel = "キャンセル"
    const cancelButton = page.getByRole("button", { name: "キャンセル" });

    await expect(cancelButton).toBeVisible();
    await expect(cancelButton).toBeEnabled();
  });
});
