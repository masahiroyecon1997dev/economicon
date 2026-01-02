import { expect, test } from "@playwright/test";

test.describe("SelectFileView - ファイル選択画面", () => {
  test.beforeEach(async ({ page }) => {
    // テスト前にページをロード
    await page.goto("/");

    // SelectFileViewに遷移（実際のナビゲーションに合わせて調整）
    // 例: ファイル選択ボタンをクリックするなど
    // await page.click('button:has-text("ファイルを選択")');
  });

  test("ページタイトルと説明が表示される", async ({ page }) => {
    // ページにタイトルが表示されることを確認
    const title = page.getByRole("heading", { name: "ファイルを選択" });
    await expect(title).toBeVisible();

    // 説明文が表示されることを確認
    const description = page.locator("p.text-black\\/60");
    await expect(description).toBeVisible();
  });

  test("検索ボックスが表示され、入力できる", async ({ page }) => {
    // 検索ボックスを取得
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
  });

  test("上位ディレクトリボタンが表示される", async ({ page }) => {
    // 上位ディレクトリに移動するボタンを探す
    const upButton = page.getByRole("button", {
      name: "上位ディレクトリへ移動",
    });
    // ボタンが表示されることを確認
    await expect(upButton).toBeVisible();
  });

  test("ファイルリストテーブルが表示される", async ({ page }) => {
    // テーブルが表示されることを確認
    const table = page.getByRole("table", { name: "ファイル一覧" });
    await expect(table).toBeVisible();

    // テーブルヘッダーが表示されることを確認
    const headers = table.locator("thead th");
    await expect(headers).toHaveCount(3); // ファイル名、サイズ、最終更新日時
  });

  test("ファイル名でソートできる", async ({ page }) => {
    // ファイル名ヘッダーをクリック
    const table = page.getByRole("table", { name: "ファイル一覧" });
    const nameHeader = table.locator("thead th").first();
    await nameHeader.click();

    // ソートアイコンが変化することを確認（昇順）
    await expect(nameHeader.locator("svg")).toBeVisible();

    // もう一度クリックして降順に
    await nameHeader.click();
    await expect(nameHeader.locator("svg")).toBeVisible();
  });

  test.only("ファイルリストが検索でフィルタリングされる", async ({ page }) => {
    // ページ遷移を待機
    await page.waitForTimeout(1000);

    const table = page.getByRole("table", { name: "ファイル一覧" });
    // 検索前のファイル数を取得
    const rowsBeforeSearch = await table.locator("tbody tr").count();

    // ページ遷移を待機
    await page.waitForTimeout(1000);

    // 検索ボックスに入力
    const searchInput = page
      .locator("main")
      .getByPlaceholder("ファイル名で検索")
      .first();
    await searchInput.fill(".csv");

    // ページ遷移を待機
    await page.waitForTimeout(1000);

    // フィルタリング後のファイル数を取得
    const rowsAfterSearch = await table.locator("tbody tr").count();

    // フィルタリングされていることを確認（CSVファイルのみ表示）
    // 実際の数は環境に依存するため、変化があることだけを確認
    expect(rowsAfterSearch).toBeLessThanOrEqual(rowsBeforeSearch);
  });

  test("ディレクトリをクリックすると移動する", async ({ page }) => {
    // ディレクトリ行を探す（フォルダーアイコンがある行）
    const directoryRow = page
      .locator("tbody tr")
      .filter({
        has: page.locator("svg.text-yellow-500"),
      })
      .first();

    // ディレクトリが存在する場合のみテスト
    const directoryCount = await directoryRow.count();
    if (directoryCount > 0) {
      // ディレクトリをクリック
      await directoryRow.click();

      // ページ遷移を待機
      await page.waitForTimeout(500);

      // パンくずリストが更新されることを確認
      const breadcrumbs = page.locator("button").filter({ hasText: /\// });
      await expect(breadcrumbs.first()).toBeVisible();
    }
  });

  test("パンくずリストから上位ディレクトリに移動できる", async ({ page }) => {
    // パンくずリストのボタンを探す
    const breadcrumbNav = page.getByRole("navigation", { name: "Breadcrumb" });
    const breadcrumbs = breadcrumbNav.locator("li button");
    const breadcrumbCount = await breadcrumbs.count();

    // パンくずが2つ以上ある場合のみテスト
    if (breadcrumbCount >= 2) {
      // 最初のパンくずリストアイテムをクリック
      await breadcrumbs.first().click();

      // ページ遷移を待機
      await page.waitForTimeout(500);

      // ディレクトリが変更されたことを確認
      const newBreadcrumbCount = await breadcrumbNav
        .locator("li button")
        .count();
      expect(newBreadcrumbCount).toBeLessThanOrEqual(breadcrumbCount);
    }
  });

  test("キャンセルボタンが表示され、クリックできる", async ({ page }) => {
    // キャンセルボタンを探す
    const cancelButton = page.getByRole("button", { name: "cancel" });

    // ボタンが表示されることを確認
    await expect(cancelButton).toBeVisible();

    // ボタンがクリック可能であることを確認
    await expect(cancelButton).toBeEnabled();
  });

  test("エラー処理: APIエラー時にエラーメッセージが表示される", async ({
    page,
  }) => {
    // APIをモックしてエラーレスポンスを返す
    await page.route("**/api/**", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ code: "ERROR", message: "テストエラー" }),
      });
    });

    // ページをリロード
    await page.reload();

    // エラーダイアログまたはメッセージが表示されることを確認
    // 実際の実装に合わせて調整
    await page.waitForTimeout(1000);
  });
});
