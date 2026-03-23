/**
 * CastColumnForm のテスト
 * - 初期 newColumnName は "price_cast"
 * - 列型 Float64 の場合は文字列オプション（cleanupWhitespace / removeCommas）が表示されない
 * - datetime/date 以外のデフォルト targetType では datetimeFormat フィールドが表示されない
 * - newColumnName を空にしてサブミット → ValidationMessages.NewColumnNameRequired が表示される
 * - API成功 → onSuccess が呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { CastColumnForm } from "./CastColumnForm";

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
    .mockResolvedValue([{ name: "price_cast", type: "Float64" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  castColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "cast-col-form",
  onIsSubmittingChange: vi.fn(),
  onSuccess: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAPI).mockReturnValue(mockApi as never);
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("CastColumnForm", () => {
  describe("初期表示", () => {
    it("newColumnName フィールドのデフォルト値は 'price_cast' である", () => {
      render(<CastColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("price_cast")).toBeInTheDocument();
    });

    it("Float64 列に対しては文字列オプション（cleanupWhitespace / removeCommas）が表示されない", () => {
      render(<CastColumnForm {...defaultProps} />);
      // isStringSource = false なのでチェックボックスは表示されない
      expect(
        screen.queryByText("CastColumnForm.CleanupWhitespace"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("CastColumnForm.RemoveCommas"),
      ).not.toBeInTheDocument();
    });

    it("デフォルト targetType (float) では datetimeFormat フィールドが表示されない", () => {
      render(<CastColumnForm {...defaultProps} />);
      // isDateTarget = false (目標型が"float") → datetimeFormat フィールドは非表示
      expect(
        screen.queryByText("CastColumnForm.DatetimeFormat"),
      ).not.toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("newColumnName を空にして blur → ValidationMessages.NewColumnNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<CastColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /CastColumnForm.NewColumnName/i,
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
      render(<CastColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /CastColumnForm.NewColumnName/i,
      });
      await user.clear(nameInput);

      const form = document.getElementById("cast-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("castColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.castColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<CastColumnForm {...defaultProps} />);

      const form = document.getElementById("cast-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "price_cast", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.castColumn.mockResolvedValue({
        code: "CAST_ERROR",
        message: "型変換に失敗しました",
      });

      render(<CastColumnForm {...defaultProps} />);

      const form = document.getElementById("cast-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("型変換に失敗しました")).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.castColumn.mockRejectedValue(new Error("接続タイムアウト"));

      render(<CastColumnForm {...defaultProps} />);

      const form = document.getElementById("cast-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
