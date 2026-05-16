import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { showMessageDialog } from "@/lib/dialog/message";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { JoinTable } from "@/components/pages/JoinTable";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("../../lib/utils/internal", () => ({
  getTableInfo: vi.fn().mockResolvedValue({
    tableName: "joined_table",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const LEFT_COLS = [
  { name: "id", type: "Int64" },
  { name: "price", type: "Float64" },
];
const RIGHT_COLS = [
  { name: "id", type: "Int64" },
  { name: "quantity", type: "Int64" },
];

const mockApi = {
  getColumnList: vi.fn(),
  createJoinTable: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "inventory"] });
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  useCurrentPageStore.setState({ currentView: "JoinTable" });

  // テーブル選択時のカラムリスト取得モック
  mockApi.getColumnList.mockImplementation(
    ({ tableName }: { tableName: string }) => {
      if (tableName === "sales") {
        return Promise.resolve({
          code: "OK",
          result: { columnInfoList: LEFT_COLS },
        });
      }
      if (tableName === "inventory") {
        return Promise.resolve({
          code: "OK",
          result: { columnInfoList: RIGHT_COLS },
        });
      }
      return Promise.resolve({ code: "OK", result: { columnInfoList: [] } });
    },
  );
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("JoinTable フォーム", () => {
  describe("初期レンダリング", () => {
    it("タイトルとセクションが表示される", () => {
      render(<JoinTable />);
      expect(screen.getByText("JoinTable.Title")).toBeInTheDocument();
    });

    it("初期状態でキーペアが1行存在する", () => {
      render(<JoinTable />);
      // キーペア行のSelect要素（左右それぞれ）が初期2つ表示される
      const combos = screen.getAllByRole("combobox");
      // 左テーブル + 右テーブル + 結合タイプ + キーペア左 + キーペア右 の Select
      expect(combos.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("バリデーション", () => {
    it("テーブル未選択でサブミットするとエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<JoinTable />);

      const submitBtn = screen.getByRole("button", {
        name: /JoinTable.RunJoin/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(screen.getAllByText("JoinTable.ErrorDataRequired").length).toBe(
          2,
        );
      });
    });

    it("出力テーブル名が空でサブミットするとエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<JoinTable />);

      // 左テーブルを選択
      const combos = screen.getAllByRole("combobox");
      await user.click(combos[0]);
      const salesOption = await screen.findByRole("option", { name: "sales" });
      await user.click(salesOption);

      // 右テーブルを選択
      await waitFor(() => expect(mockApi.getColumnList).toHaveBeenCalled());
      const combos2 = screen.getAllByRole("combobox");
      await user.click(combos2[1]);
      const inventoryOption = await screen.findByRole("option", {
        name: "inventory",
      });
      await user.click(inventoryOption);

      // 出力名を空にする
      const newTableNameInput =
        screen.getByPlaceholderText(/NewDataName|新しいデータ名/i);
      await user.clear(newTableNameInput);

      const submitBtn = screen.getByRole("button", {
        name: /JoinTable.RunJoin/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("JoinTable.ErrorNewDataNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("自動補完", () => {
    it("同名列があれば自動提案が適用される", async () => {
      const user = userEvent.setup();
      render(<JoinTable />);

      const combos = screen.getAllByRole("combobox");
      await user.click(combos[0]);
      const salesOption = await screen.findByRole("option", { name: "sales" });
      await user.click(salesOption);

      await waitFor(() => expect(mockApi.getColumnList).toHaveBeenCalled());

      const combos2 = screen.getAllByRole("combobox");
      await user.click(combos2[1]);
      const inventoryOption = await screen.findByRole("option", {
        name: "inventory",
      });
      await user.click(inventoryOption);

      await waitFor(() => {
        // 自動提案が適用され、結合テーブル名が自動設定される
        expect(
          screen.getByDisplayValue("sales_inventory_joined"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("キーペア追加", () => {
    it("キーペア追加ボタンをクリックすると行が増える", async () => {
      const user = userEvent.setup();
      render(<JoinTable />);

      const addBtn = screen.getByRole("button", {
        name: /JoinTable.AddKeyPair|キーを追加/i,
      });
      await user.click(addBtn);

      // キーペア行が増えたことを確認
      const deleteKeyBtns = screen.getAllByRole("button", {
        name: /RemoveKeyPair|キーペアを削除/i,
      });
      expect(deleteKeyBtns.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("API成功時", () => {
    it("createJoinTable が OK → DataPreview に遷移する", async () => {
      mockApi.createJoinTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "sales_inventory_joined" },
      });
      const user = userEvent.setup();
      render(<JoinTable />);

      // 左テーブルを選択
      const combos = screen.getAllByRole("combobox");
      await user.click(combos[0]);
      const salesOption = await screen.findByRole("option", { name: "sales" });
      await user.click(salesOption);

      await waitFor(() => expect(mockApi.getColumnList).toHaveBeenCalled());

      // 右テーブルを選択
      const combos2 = screen.getAllByRole("combobox");
      await user.click(combos2[1]);
      const inventoryOption = await screen.findByRole("option", {
        name: "inventory",
      });
      await user.click(inventoryOption);

      await waitFor(() => {
        expect(
          screen.getByDisplayValue("sales_inventory_joined"),
        ).toBeInTheDocument();
      });

      const submitBtn = screen.getByRole("button", {
        name: /JoinTable.RunJoin/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(mockApi.createJoinTable).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });

  describe("API失敗時", () => {
    it("createJoinTable がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.createJoinTable.mockRejectedValue(new Error("ジョイン失敗"));
      const user = userEvent.setup();
      render(<JoinTable />);

      const combos = screen.getAllByRole("combobox");
      await user.click(combos[0]);
      const salesOption = await screen.findByRole("option", { name: "sales" });
      await user.click(salesOption);

      await waitFor(() => expect(mockApi.getColumnList).toHaveBeenCalled());

      const combos2 = screen.getAllByRole("combobox");
      await user.click(combos2[1]);
      const inventoryOption = await screen.findByRole("option", {
        name: "inventory",
      });
      await user.click(inventoryOption);

      await waitFor(() => {
        expect(
          screen.getByDisplayValue("sales_inventory_joined"),
        ).toBeInTheDocument();
      });

      const submitBtn = screen.getByRole("button", {
        name: /JoinTable.RunJoin/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ジョイン失敗",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<JoinTable />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
