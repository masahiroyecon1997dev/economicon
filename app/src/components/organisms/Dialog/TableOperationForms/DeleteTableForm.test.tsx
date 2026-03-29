import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { useCurrentPageStore } from "../../../../stores/currentView";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { DeleteTableForm } from "./DeleteTableForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
  Trans: ({
    i18nKey,
    values,
  }: {
    i18nKey: string;
    values?: Record<string, string>;
  }) => `${i18nKey}::${values?.tableName ?? ""}`,
}));

vi.mock("../../../../api/endpoints");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  deleteTable: vi.fn(),
  getTableList: vi.fn(),
};

const defaultProps = {
  tableName: "sales",
  onSuccess: vi.fn(),
  formId: "delete-form",
  onIsSubmittingChange: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "costs"] });
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [],
        totalRows: 0,
        isActive: true,
      },
    ],
    activeTableName: "sales",
  });
  useCurrentPageStore.setState({ currentView: "DataPreview" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DeleteTableForm", () => {
  describe("API成功時", () => {
    it("deleteTable が OK → removeTableInfo が呼ばれ、onSuccess が呼ばれる", async () => {
      mockApi.deleteTable.mockResolvedValue({ code: "OK", result: {} });
      mockApi.getTableList.mockResolvedValue({
        code: "OK",
        result: { tableNameList: ["costs"] },
      });

      render(<DeleteTableForm {...defaultProps} />);

      const form = document.getElementById("delete-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalled();
      });

      // テーブル一覧からsalesが消える
      expect(useTableListStore.getState().tableList).toEqual(["costs"]);
    });

    it("アクティブなテーブルを削除 → currentViewがImportDataFileに変わる", async () => {
      mockApi.deleteTable.mockResolvedValue({ code: "OK", result: {} });
      mockApi.getTableList.mockResolvedValue({
        code: "OK",
        result: { tableNameList: ["costs"] },
      });

      render(<DeleteTableForm {...defaultProps} />);

      const form = document.getElementById("delete-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(useCurrentPageStore.getState().currentView).toBe(
          "ImportDataFile",
        );
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert にAPIのmessageが表示される", async () => {
      mockApi.deleteTable.mockResolvedValue({
        code: "TABLE_NOT_FOUND",
        message: "テーブルが存在しません",
      });

      render(<DeleteTableForm {...defaultProps} />);

      const form = document.getElementById("delete-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("テーブルが存在しません")).toBeInTheDocument();
      });
      expect(defaultProps.onSuccess).not.toHaveBeenCalled();
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.deleteTable.mockRejectedValue(new Error("サーバーエラー"));

      render(<DeleteTableForm {...defaultProps} />);

      const form = document.getElementById("delete-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("サーバーエラー")).toBeInTheDocument();
      });
    });
  });
});
