import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { showMessageDialog } from "@/lib/dialog/message";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { UnionTable as UnionTablePage } from "@/components/pages/UnionTable";

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
    tableName: "union_result",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  getColumnList: vi.fn(),
  createUnionTable: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({
    tableList: ["sales_q1", "sales_q2", "sales_q3"],
  });
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  useCurrentPageStore.setState({ currentView: "UnionTable" });

  mockApi.getColumnList.mockResolvedValue({
    code: "OK",
    result: {
      columnInfoList: [
        { name: "id", type: "Int64" },
        { name: "price", type: "Float64" },
      ],
    },
  });
});

const addTable = async (
  user: ReturnType<typeof userEvent.setup>,
  name: string,
) => {
  const combobox = screen.getByRole("combobox");
  await user.click(combobox);
  const option = await screen.findByRole("option", { name });
  await user.click(option);

  const addBtn = screen.getByRole("button", {
    name: /UnionTable.Add/i,
  });
  await user.click(addBtn);
};

const waitForCommonColumns = async () => {
  await screen.findByRole("checkbox", { name: "id" });
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("UnionTable フォーム", () => {
  describe("初期レンダリング", () => {
    it("タイトルとデータ選択セクションが表示される", () => {
      render(<UnionTablePage />);
      expect(screen.getByText("UnionTable.Title")).toBeInTheDocument();
      expect(screen.getByText("UnionTable.SelectDataList")).toBeInTheDocument();
    });

    it("初期状態ではテーブルが追加されていない", () => {
      render(<UnionTablePage />);
      // 追加済みテーブルのバッジが0個
      const removeBtns = screen.queryAllByRole("button", {
        name: /RemoveTable|削除/i,
      });
      expect(removeBtns).toHaveLength(0);
    });
  });

  describe("テーブル追加", () => {
    it("テーブルを選択して追加ボタンをクリックするとリストに追加される", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");

      await waitFor(() => {
        expect(screen.getByText("sales_q1")).toBeInTheDocument();
      });
    });

    it("同じテーブルは重複追加されない", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");

      await waitFor(() => {
        const occurrences = screen
          .getAllByText("sales_q1")
          .filter((el) => el.tagName !== "OPTION");
        expect(occurrences).toHaveLength(1);
      });
    });

    it("テーブルを削除するとリストから消える", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");

      await waitFor(() =>
        expect(screen.getByText("sales_q1")).toBeInTheDocument(),
      );

      const removeBtn = screen.getByRole("button", {
        name: /UnionTable.RemoveData|削除/i,
      });
      await user.click(removeBtn);

      await waitFor(() => {
        expect(screen.queryByText("sales_q1")).toBeNull();
      });
    });
  });

  describe("バリデーション", () => {
    it("テーブルが1件以下でサブミットするとエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");

      const submitBtn = screen.getByRole("button", {
        name: /UnionTable.RunUnion/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("UnionTable.ErrorDataRequired"),
        ).toBeInTheDocument();
      });
    });

    it("出力テーブル名が空でサブミットするとエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");
      await addTable(user, "sales_q2");
      await waitForCommonColumns();

      // 自動設定される出力名をクリア
      const newNameInput = screen.getByRole("textbox");
      await user.clear(newNameInput);

      const submitBtn = screen.getByRole("button", {
        name: /UnionTable.RunUnion/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("UnionTable.ErrorNewDataNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("createUnionTable が OK → DataPreview に遷移する", async () => {
      mockApi.createUnionTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "union_result" },
      });
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");
      await addTable(user, "sales_q2");
      await waitForCommonColumns();

      const submitBtn = screen.getByRole("button", {
        name: /UnionTable.RunUnion/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(mockApi.createUnionTable).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });

  describe("API失敗時", () => {
    it("createUnionTable がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.createUnionTable.mockRejectedValue(new Error("ユニオン失敗"));
      const user = userEvent.setup();
      render(<UnionTablePage />);

      await addTable(user, "sales_q1");
      await addTable(user, "sales_q2");
      await waitForCommonColumns();

      const submitBtn = screen.getByRole("button", {
        name: /UnionTable.RunUnion/i,
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ユニオン失敗",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<UnionTablePage />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
