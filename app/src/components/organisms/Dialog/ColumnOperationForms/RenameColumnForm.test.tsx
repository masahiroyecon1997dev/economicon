import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { RenameColumnForm } from "./RenameColumnForm";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("../../../../api/endpoints");

vi.mock("./fetchUpdatedColumnList", () => ({
  fetchUpdatedColumnList: vi
    .fn()
    .mockResolvedValue([{ name: "new_price", type: "Float64" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  renameColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "rename-col-form",
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
describe("RenameColumnForm", () => {
  describe("バリデーション", () => {
    it("入力後にクリアすると onChange バリデーションでエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<RenameColumnForm {...defaultProps} />);

      const input = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      // デフォルト値は空なので、一度入力してから空にする（空への clear は change を発火しないため）
      await user.type(input, "temp_name");
      await user.clear(input); // onChange fires with "" → isTouched=true → validator runs

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("空文字でフォームサブミット → onSubmit バリデーションエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<RenameColumnForm {...defaultProps} />);

      const input = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.clear(input);

      const form = document.getElementById("rename-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("renameColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.renameColumn.mockResolvedValue({ code: "OK", result: {} });

      const user = userEvent.setup();
      render(<RenameColumnForm {...defaultProps} />);

      const input = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.clear(input);
      await user.type(input, "new_price");

      const form = document.getElementById("rename-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "new_price", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert にAPIのmessageが表示される", async () => {
      mockApi.renameColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });

      const user = userEvent.setup();
      render(<RenameColumnForm {...defaultProps} />);

      const input = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.clear(input);
      await user.type(input, "price"); // 既存と同名

      const form = document.getElementById("rename-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その列名はすでに存在します"),
        ).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.renameColumn.mockRejectedValue(new Error("サーバーエラー"));

      const user = userEvent.setup();
      render(<RenameColumnForm {...defaultProps} />);

      const input = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.clear(input);
      await user.type(input, "new_price");

      const form = document.getElementById("rename-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("サーバーエラー")).toBeInTheDocument();
      });
    });
  });
});
