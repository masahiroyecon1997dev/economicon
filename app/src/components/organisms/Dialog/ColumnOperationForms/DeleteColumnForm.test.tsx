/**
 * DeleteColumnForm のテスト
 * - DangerAlert に column.name が表示されること
 * - API成功 → onSuccess が呼ばれること
 * - API失敗 → ErrorAlert に APIのmessage が表示されること
 * - throw → ErrorAlert にエラーメッセージが表示されること
 */
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { DeleteColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/DeleteColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
  Trans: ({ values }: { i18nKey?: string; values?: Record<string, string> }) =>
    values?.columnName ? <span>{values.columnName}</span> : null,
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi
    .fn()
    .mockResolvedValue([{ name: "qty", type: "Int64" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  deleteColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "delete-col-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DeleteColumnForm", () => {
  describe("初期表示", () => {
    it("DangerAlert に削除対象の列名が表示される", () => {
      render(<DeleteColumnForm {...defaultProps} />);

      // Trans コンポーネントが values.columnName = "price" を表示する
      expect(screen.getByText("price")).toBeInTheDocument();
    });
  });

  describe("API成功時", () => {
    it("deleteColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.deleteColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<DeleteColumnForm {...defaultProps} />);

      const form = document.getElementById("delete-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "qty", type: "Int64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.deleteColumn.mockResolvedValue({
        code: "COLUMN_NOT_FOUND",
        message: "列が見つかりません",
      });

      render(<DeleteColumnForm {...defaultProps} />);

      const form = document.getElementById("delete-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("列が見つかりません")).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.deleteColumn.mockRejectedValue(
        new Error("サーバーへの接続に失敗しました"),
      );

      render(<DeleteColumnForm {...defaultProps} />);

      const form = document.getElementById("delete-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("サーバーへの接続に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });
});
