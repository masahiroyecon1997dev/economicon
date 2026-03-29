import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { RenameTableForm } from "./RenameTableForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("../../../../api/endpoints");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  renameTable: vi.fn(),
  getTableList: vi.fn(),
};

const defaultProps = {
  tableName: "sales",
  onSuccess: vi.fn(),
  formId: "rename-form",
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
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("RenameTableForm", () => {
  describe("バリデーション", () => {
    it("空文字でサブミット → DataNameRequiredエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("129文字の名前でサブミット → DataNameTooLongエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "a".repeat(129));

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameTooLong"),
        ).toBeInTheDocument();
      });
    });

    it("制御文字（\\x01）を含む名前でサブミット → DataNameInvalidCharsエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      // 制御文字は userEvent.type では入力できないため直接値を変更
      await user.click(input);
      Object.defineProperty(input, "value", {
        value: "abc\x01def",
        writable: true,
      });
      input.dispatchEvent(new Event("input", { bubbles: true }));

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameInvalidChars"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("renameTable が OK → onSuccess が呼ばれ、テーブルリストが更新される", async () => {
      mockApi.renameTable.mockResolvedValue({ code: "OK", result: {} });
      mockApi.getTableList.mockResolvedValue({
        code: "OK",
        result: { tableNameList: ["new_sales", "costs"] },
      });

      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "new_sales");

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalled();
      });
      expect(useTableListStore.getState().tableList).toEqual([
        "new_sales",
        "costs",
      ]);
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert にAPIのmessageが表示される", async () => {
      mockApi.renameTable.mockResolvedValue({
        code: "DUPLICATE_TABLE_NAME",
        message: "その名前はすでに使われています",
      });

      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "costs");

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その名前はすでに使われています"),
        ).toBeInTheDocument();
      });
      expect(defaultProps.onSuccess).not.toHaveBeenCalled();
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.renameTable.mockRejectedValue(new Error("タイムアウト"));

      const user = userEvent.setup();
      render(<RenameTableForm {...defaultProps} />);

      const input = screen.getByRole("textbox");
      await user.clear(input);
      await user.type(input, "new_sales");

      const form = document.getElementById("rename-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
