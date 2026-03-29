/**
 * TransformColumnForm のテスト
 * - 初期 method="log" → base フィールド（id="tf-base"）が表示される
 * - 初期 method="log" → exponent / degree フィールドが表示されない
 * - 初期 newColumnName は "log_price"
 * - newColumnName を空にして blur → ValidationMessages.NewColumnNameRequired が表示される
 * - API成功 → onSuccess が呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { TransformColumnForm } from "./TransformColumnForm";

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
    .mockResolvedValue([{ name: "log_price", type: "Float64" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  transformColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "transform-col-form",
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
describe("TransformColumnForm", () => {
  describe("初期表示 (method = log)", () => {
    it("newColumnName フィールドのデフォルト値は 'log_price' である", () => {
      render(<TransformColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("log_price")).toBeInTheDocument();
    });

    it("method='log' では TransformColumnForm.Base フィールドが表示される", () => {
      render(<TransformColumnForm {...defaultProps} />);
      expect(screen.getByText("TransformColumnForm.Base")).toBeInTheDocument();
    });

    it("method='log' では TransformColumnForm.Exponent フィールドが表示されない", () => {
      render(<TransformColumnForm {...defaultProps} />);
      expect(
        screen.queryByText("TransformColumnForm.Exponent"),
      ).not.toBeInTheDocument();
    });

    it("method='log' では TransformColumnForm.Degree フィールドが表示されない", () => {
      render(<TransformColumnForm {...defaultProps} />);
      expect(
        screen.queryByText("TransformColumnForm.Degree"),
      ).not.toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("newColumnName を空にして blur → ValidationMessages.NewColumnNameRequired が表示される", async () => {
      const user = userEvent.setup();
      render(<TransformColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /TransformColumnForm.NewColumnName/i,
      });
      await user.clear(nameInput);
      await user.tab(); // blur → isTouched = true

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("newColumnName を空にしてサブミット → onSuccess が呼ばれない", async () => {
      const user = userEvent.setup();
      render(<TransformColumnForm {...defaultProps} />);

      const nameInput = screen.getByRole("textbox", {
        name: /TransformColumnForm.NewColumnName/i,
      });
      await user.clear(nameInput);

      const form = document.getElementById("transform-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      // バリデーションで阻止されるため API は呼ばれない
      await waitFor(() => {
        expect(mockApi.transformColumn).not.toHaveBeenCalled();
      });
    });
  });

  describe("API成功時", () => {
    it("transformColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.transformColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<TransformColumnForm {...defaultProps} />);

      const form = document.getElementById("transform-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "log_price", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.transformColumn.mockResolvedValue({
        code: "TRANSFORM_ERROR",
        message: "変換に失敗しました",
      });

      render(<TransformColumnForm {...defaultProps} />);

      const form = document.getElementById("transform-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("変換に失敗しました")).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.transformColumn.mockRejectedValue(new Error("接続タイムアウト"));

      render(<TransformColumnForm {...defaultProps} />);

      const form = document.getElementById("transform-col-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
