/**
 * FilterColumnForm のテスト
 * - newTableName デフォルト値は "sales_filtered"
 * - 初期状態では条件2は非表示
 * - 「条件追加」ボタンクリック → 条件2・論理演算子が表示される
 * - 条件2の削除ボタンクリック → 条件2・論理演算子が非表示になる
 * - newTableName を空にして blur → ValidationMessages.DataNameRequired が表示される
 * - newTableName を空にしてサブミット → ValidationMessages.DataNameRequired が表示される
 * - API成功 → filterTable が呼ばれ、onSuccess が allColumns を引数に呼ばれ、テーブルリストが更新される
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { getTableInfo } from "@/lib/utils/internal";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { FilterColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/FilterColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("../../../../lib/utils/internal");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  filterTable: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "filter-col-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

const salesColumns = [{ name: "price", type: "Float64" }];

const mockTableInfo = {
  tableName: "sales_filtered",
  columnList: salesColumns,
  totalRows: 50,
  isActive: true,
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  vi.mocked(getTableInfo).mockResolvedValue(mockTableInfo);
  useTableListStore.setState({ tableList: ["sales"] });
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: salesColumns,
        totalRows: 100,
        isActive: true,
      },
    ],
    activeTableName: "sales",
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("FilterColumnForm", () => {
  describe("初期表示", () => {
    it("newTableName フィールドのデフォルト値は 'sales_filtered' である", () => {
      render(<FilterColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("sales_filtered")).toBeInTheDocument();
    });

    it("条件2は初期状態では表示されない", () => {
      render(<FilterColumnForm {...defaultProps} />);
      expect(
        screen.queryByText("FilterColumnForm.Condition2"),
      ).not.toBeInTheDocument();
    });
  });

  describe("条件2の追加・削除", () => {
    it("「条件追加」ボタンをクリックすると条件2と論理演算子が表示される", async () => {
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      await user.click(screen.getByTestId("filter-add-condition"));

      await waitFor(() => {
        expect(
          screen.getByText("FilterColumnForm.Condition2"),
        ).toBeInTheDocument();
      });
      expect(
        screen.getByText("FilterColumnForm.LogicalOperator"),
      ).toBeInTheDocument();
    });

    it("条件2の削除ボタンをクリックすると条件2と論理演算子が非表示になる", async () => {
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      await user.click(screen.getByTestId("filter-add-condition"));
      await waitFor(() => screen.getByText("FilterColumnForm.Condition2"));

      await user.click(screen.getByTestId("filter-remove-condition"));

      await waitFor(() => {
        expect(
          screen.queryByText("FilterColumnForm.Condition2"),
        ).not.toBeInTheDocument();
      });
      expect(
        screen.queryByText("FilterColumnForm.LogicalOperator"),
      ).not.toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("newTableName を空にして blur → ValidationMessages.DataNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /FilterColumnForm\.NewTableName/i,
      });
      await user.clear(nameInput);
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("newTableName を空にしてサブミット → ValidationMessages.DataNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /FilterColumnForm\.NewTableName/i,
      });
      await user.clear(nameInput);

      const form = document.getElementById("filter-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("filterTable が OK → onSuccess が allColumns を引数に呼ばれ、テーブルリストが更新される", async () => {
      mockApi.filterTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "sales_filtered" },
      });
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      const c1ValueInput = screen.getByRole("textbox", {
        name: /FilterColumnForm\.CompareValue/i,
      });
      await user.type(c1ValueInput, "100");

      const form = document.getElementById("filter-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => expect(mockApi.filterTable).toHaveBeenCalled());
      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith(salesColumns);
      });
      expect(useTableListStore.getState().tableList).toContain(
        "sales_filtered",
      );
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.filterTable.mockResolvedValue({
        code: "TABLE_NAME_CONFLICT",
        message: "その名前のテーブルはすでに存在します",
      });
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      const c1ValueInput = screen.getByRole("textbox", {
        name: /FilterColumnForm\.CompareValue/i,
      });
      await user.type(c1ValueInput, "100");

      const form = document.getElementById("filter-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その名前のテーブルはすでに存在します"),
        ).toBeInTheDocument();
      });
      expect(defaultProps.onSuccess).not.toHaveBeenCalled();
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.filterTable.mockRejectedValue(new Error("接続タイムアウト"));
      const user = userEvent.setup();
      render(<FilterColumnForm {...defaultProps} />);

      const c1ValueInput = screen.getByRole("textbox", {
        name: /FilterColumnForm\.CompareValue/i,
      });
      await user.type(c1ValueInput, "100");

      const form = document.getElementById("filter-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
