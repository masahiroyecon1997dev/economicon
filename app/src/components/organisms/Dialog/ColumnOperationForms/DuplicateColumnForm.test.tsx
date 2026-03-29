/**
 * DuplicateColumnForm のテスト
 * - 初期 newColumnName は "price_copy"
 * - newColumnName を空にして blur → ValidationMessages.NewColumnNameRequired が表示される
 * - newColumnName を空にしてサブミット → ValidationMessages.NewColumnNameRequired が表示される
 * - API成功 → onSuccess が呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { DuplicateColumnForm } from "./DuplicateColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi.fn().mockResolvedValue([
    { name: "price", type: "Float64" },
    { name: "price_copy", type: "Float64" },
  ]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  duplicateColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "dup-col-form",
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
describe("DuplicateColumnForm", () => {
  describe("初期表示", () => {
    it("newColumnName フィールドのデフォルト値は 'price_copy' である", () => {
      render(<DuplicateColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("price_copy")).toBeInTheDocument();
    });

    it("複製元の列名 (price) が表示される", () => {
      render(<DuplicateColumnForm {...defaultProps} />);
      // RenameColumnForm.CurrentColumnName ラベル下に price が表示される
      expect(screen.getByText("price")).toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("newColumnName を空にして blur → ValidationMessages.NewColumnNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<DuplicateColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /DuplicateColumnForm.NewColumnName/i,
      });
      await user.clear(nameInput);
      await user.tab(); // blur → isTouched = true

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("newColumnName を空にしてサブミット → ValidationMessages.NewColumnNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<DuplicateColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /DuplicateColumnForm.NewColumnName/i,
      });
      await user.clear(nameInput);

      const form = document.getElementById("dup-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("duplicateColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.duplicateColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<DuplicateColumnForm {...defaultProps} />);

      const form = document.getElementById("dup-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "price", type: "Float64" },
          { name: "price_copy", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.duplicateColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });

      render(<DuplicateColumnForm {...defaultProps} />);

      const form = document.getElementById("dup-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その列名はすでに存在します"),
        ).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.duplicateColumn.mockRejectedValue(
        new Error("サーバーへの接続に失敗しました"),
      );

      render(<DuplicateColumnForm {...defaultProps} />);

      const form = document.getElementById("dup-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("サーバーへの接続に失敗しました"),
        ).toBeInTheDocument();
      });
    });
  });
});
