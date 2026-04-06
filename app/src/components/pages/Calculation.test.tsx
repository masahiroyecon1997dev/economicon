import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { showMessageDialog } from "@/lib/dialog/message";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { Calculation } from "@/components/pages/Calculation";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      if (!opts) return key;
      return Object.entries(opts).reduce(
        (s, [k, v]) => s.replace(`{{${k}}}`, v),
        key,
      );
    },
  }),
}));

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("../../lib/utils/internal", () => ({
  getTableInfo: vi.fn().mockResolvedValue({
    tableName: "sales",
    columnList: [{ name: "price", type: "Float64" }],
    totalRows: 10,
    isActive: true,
  }),
}));
vi.mock("../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({
    selectedTableName: "sales",
    setSelectedTableName: vi.fn(),
    columnList: [{ name: "price", type: "Float64" }],
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  calculateColumn: vi.fn(),
  getColumnList: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "costs"] });
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [{ name: "price", type: "Float64" }],
        totalRows: 10,
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
describe("Calculation フォーム", () => {
  describe("バリデーション", () => {
    it("新列名が空のままサブミットするとバリデーションエラーが表示される", async () => {
      render(<Calculation />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.NewColumnNameRequired"),
        ).toBeInTheDocument();
      });
    });

    it("計算式が空のままサブミットするとバリデーションエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<Calculation />);

      const newColInput = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.type(newColInput, "result_col");

      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.CalculationExpressionRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("calculateColumn が OK → DataPreviewへ遷移する", async () => {
      mockApi.calculateColumn.mockResolvedValue({ code: "OK", result: {} });
      const user = userEvent.setup();
      render(<Calculation />);

      const newColInput = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.type(newColInput, "new_col");

      const textarea = screen.getByRole("textbox", {
        name: /CalculationExpression|計算式/i,
      });
      await user.type(textarea, "price * 2");

      await submitForm();

      await waitFor(() => {
        expect(mockApi.calculateColumn).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → APIのmessageでダイアログを表示する", async () => {
      mockApi.calculateColumn.mockResolvedValue({
        code: "COLUMN_NAME_CONFLICT",
        message: "その列名はすでに存在します",
      });
      const user = userEvent.setup();
      render(<Calculation />);

      const newColInput = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.type(newColInput, "price");

      const textarea = screen.getByRole("textbox", {
        name: /CalculationExpression|計算式/i,
      });
      await user.type(textarea, "price * 2");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "その列名はすでに存在します",
        );
      });
    });

    it("APIがthrowした場合 → extractApiErrorMessage経由でダイアログを表示する", async () => {
      mockApi.calculateColumn.mockRejectedValue(
        new Error("ネットワークエラー"),
      );
      const user = userEvent.setup();
      render(<Calculation />);

      const newColInput = screen.getByRole("textbox", {
        name: /NewColumnName|新しい列名/i,
      });
      await user.type(newColInput, "new_col");

      const textarea = screen.getByRole("textbox", {
        name: /CalculationExpression|計算式/i,
      });
      await user.type(textarea, "price * 2");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ネットワークエラー",
        );
      });
    });
  });
});
