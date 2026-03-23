import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { useTableListStore } from "../../../../stores/tableList";
import { DuplicateTableForm } from "./DuplicateTableForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  duplicateTable: vi.fn(),
  getTableList: vi.fn(),
};

const defaultProps = {
  tableName: "sales",
  onSuccess: vi.fn(),
  formId: "duplicate-form",
  onIsSubmittingChange: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DuplicateTableForm", () => {
  describe("デフォルト値", () => {
    it("初期値は 'sales_copy' がセットされている", () => {
      render(<DuplicateTableForm {...defaultProps} />);
      const input = screen.getByRole("textbox");
      expect(input).toHaveValue("sales_copy");
    });
  });

  describe("バリデーション", () => {
    it("空文字でサブミット → DataNameRequiredエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<DuplicateTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);

      const form = document.getElementById("duplicate-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("129文字でサブミット → DataNameTooLongエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<DuplicateTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "a".repeat(129));

      const form = document.getElementById("duplicate-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameTooLong"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("duplicateTable が OK → テーブルリスト更新・onSuccess が呼ばれる", async () => {
      mockApi.duplicateTable.mockResolvedValue({ code: "OK", result: {} });
      mockApi.getTableList.mockResolvedValue({
        code: "OK",
        result: { tableNameList: ["sales", "sales_copy"] },
      });

      render(<DuplicateTableForm {...defaultProps} />);

      const form = document.getElementById("duplicate-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalled();
      });
      expect(useTableListStore.getState().tableList).toEqual([
        "sales",
        "sales_copy",
      ]);
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert にAPIのmessageが表示される", async () => {
      mockApi.duplicateTable.mockResolvedValue({
        code: "DUPLICATE_TABLE_NAME",
        message: "同名のテーブルが存在します",
      });

      render(<DuplicateTableForm {...defaultProps} />);

      const form = document.getElementById("duplicate-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("同名のテーブルが存在します"),
        ).toBeInTheDocument();
      });
      expect(defaultProps.onSuccess).not.toHaveBeenCalled();
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.duplicateTable.mockRejectedValue(new Error("接続に失敗しました"));

      render(<DuplicateTableForm {...defaultProps} />);

      const form = document.getElementById("duplicate-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続に失敗しました")).toBeInTheDocument();
      });
    });
  });
});
