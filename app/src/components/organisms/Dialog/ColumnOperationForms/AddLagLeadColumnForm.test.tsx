/**
 * AddLagLeadColumnForm のテスト
 * - 初期 newColumnName デフォルト値は "lag1_price"
 * - periods=0 → onChange バリデーションエラー（AddLagLeadColumnForm.PeriodsError）
 * - 非整数入力 → onChange バリデーションエラー
 * - periods=-2 → newColumnName が "lag2_price" に自動更新される
 * - API成功 → onSuccess が呼ばれる
 * - API失敗 → ErrorAlert に APIのmessage が表示される
 * - throw → ErrorAlert にエラーメッセージが表示される
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { AddLagLeadColumnForm } from "@/components/organisms/Dialog/ColumnOperationForms/AddLagLeadColumnForm";

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
    .mockResolvedValue([{ name: "lag1_price", type: "Float64" }]),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  addLagLeadColumn: vi.fn(),
};

const column = { name: "price", type: "Float64" };

const defaultProps = {
  tableName: "sales",
  column,
  formId: "add-lag-form",
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
describe("AddLagLeadColumnForm", () => {
  describe("初期表示", () => {
    it("新列名フィールドのデフォルト値は 'lag1_price' である", () => {
      render(<AddLagLeadColumnForm {...defaultProps} />);
      expect(screen.getByDisplayValue("lag1_price")).toBeInTheDocument();
    });
  });

  describe("onChange バリデーション（periods フィールド）", () => {
    it("periods に 0 を入力して blur → AddLagLeadColumnForm.PeriodsError が表示される", async () => {
      const user = userEvent.setup();
      render(<AddLagLeadColumnForm {...defaultProps} />);

      const periodsInput = screen.getByRole("spinbutton", {
        name: /AddLagLeadColumnForm.Periods/i,
      });
      await user.clear(periodsInput);
      await user.type(periodsInput, "0");
      await user.tab(); // blur → isTouched = true

      await waitFor(() => {
        expect(
          screen.getByText("AddLagLeadColumnForm.PeriodsError"),
        ).toBeInTheDocument();
      });
    });

    it("小数（非整数のピリオドのみ）を入力して blur → PeriodsError が表示される", async () => {
      const user = userEvent.setup();
      render(<AddLagLeadColumnForm {...defaultProps} />);

      const periodsInput = screen.getByRole("spinbutton", {
        name: /AddLagLeadColumnForm.Periods/i,
      });
      // type="number" への非数値のキー入力はブラウザが弾くが、
      // fireEvent で直接 valueAsNumber を NaN にできる
      await user.clear(periodsInput);
      fireEvent.change(periodsInput, { target: { value: "abc" } });
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText("AddLagLeadColumnForm.PeriodsError"),
        ).toBeInTheDocument();
      });
    });

    it("periods を -2 に変更すると newColumnName が 'lag2_price' に自動更新される", async () => {
      const user = userEvent.setup();
      render(<AddLagLeadColumnForm {...defaultProps} />);

      const periodsInput = screen.getByRole("spinbutton", {
        name: /AddLagLeadColumnForm.Periods/i,
      });
      await user.clear(periodsInput);
      await user.type(periodsInput, "-2");

      await waitFor(() => {
        expect(screen.getByDisplayValue("lag2_price")).toBeInTheDocument();
      });
    });

    it("periods を 3 に変更すると newColumnName が 'lead3_price' に自動更新される", async () => {
      const user = userEvent.setup();
      render(<AddLagLeadColumnForm {...defaultProps} />);

      const periodsInput = screen.getByRole("spinbutton", {
        name: /AddLagLeadColumnForm.Periods/i,
      });
      await user.clear(periodsInput);
      await user.type(periodsInput, "3");

      await waitFor(() => {
        expect(screen.getByDisplayValue("lead3_price")).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("addLagLeadColumn が OK → onSuccess が最新 columnList を引数に呼ばれる", async () => {
      mockApi.addLagLeadColumn.mockResolvedValue({ code: "OK", result: {} });

      render(<AddLagLeadColumnForm {...defaultProps} />);

      const form = document.getElementById("add-lag-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(defaultProps.onSuccess).toHaveBeenCalledWith([
          { name: "lag1_price", type: "Float64" },
        ]);
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → ErrorAlert に APIのmessage が表示される", async () => {
      mockApi.addLagLeadColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });

      render(<AddLagLeadColumnForm {...defaultProps} />);

      const form = document.getElementById("add-lag-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(
          screen.getByText("その列名はすでに存在します"),
        ).toBeInTheDocument();
      });
    });

    it("APIがthrowした場合 → ErrorAlert にエラーメッセージが表示される", async () => {
      mockApi.addLagLeadColumn.mockRejectedValue(new Error("接続タイムアウト"));

      render(<AddLagLeadColumnForm {...defaultProps} />);

      const form = document.getElementById("add-lag-form")!;
      form.dispatchEvent(new Event("submit", { bubbles: true }));

      await waitFor(() => {
        expect(screen.getByText("接続タイムアウト")).toBeInTheDocument();
      });
    });
  });
});
