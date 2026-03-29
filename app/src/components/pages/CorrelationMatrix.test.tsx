import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act, beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import { CorrelationMatrix } from "./CorrelationMatrix";

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
    tableName: "corr_result",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));
vi.mock("../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({
    selectedTableName: "",
    setSelectedTableName: vi.fn(),
    columnList: [
      { name: "price", type: "Float64" },
      { name: "quantity", type: "Float64" },
    ],
    setColumnList: vi.fn(),
  }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  createCorrelationTable: vi.fn(),
  getColumnList: vi.fn(),
};

const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "costs"] });
  useTableInfosStore.setState({
    tableInfos: [],
    activeTableName: null,
  });
  useCurrentPageStore.setState({ currentView: "CorrelationMatrix" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("CorrelationMatrix フォーム", () => {
  describe("バリデーション", () => {
    it("テーブル未選択でサブミットするとエラーが表示される", async () => {
      render(<CorrelationMatrix />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("CorrelationMatrix.ErrorDataRequired"),
        ).toBeInTheDocument();
      });
    });

    it("出力データ名が空のままサブミットするとエラーが表示される", async () => {
      render(<CorrelationMatrix />);
      // columnNames はフック経由で自動セットされる想定
      await submitForm();

      await waitFor(() => {
        // テーブル未選択エラーと出力名エラーが出る
        expect(
          screen.getAllByText(/ErrorDataRequired|ErrorOutputNameRequired/),
        ).toBeTruthy();
      });
    });
  });

  describe("詳細オプション accordion", () => {
    it("詳細オプションボタンをクリックするとオプションが展開される", async () => {
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const optionBtn = screen.getByRole("button", {
        name: /AdvancedOptions/,
      });
      expect(screen.queryByText("CorrelationMatrix.MethodLabel")).toBeNull();
      await user.click(optionBtn);

      await waitFor(() => {
        expect(
          screen.getByText("CorrelationMatrix.MethodLabel"),
        ).toBeInTheDocument();
      });
    });

    it("詳細オプションを2回クリックすると折りたたまれる", async () => {
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const optionBtn = screen.getByRole("button", {
        name: /AdvancedOptions/,
      });
      await user.click(optionBtn);
      await user.click(optionBtn);

      await waitFor(() => {
        expect(screen.queryByText("CorrelationMatrix.MethodLabel")).toBeNull();
      });
    });
  });

  describe("API成功時", () => {
    it("createCorrelationTable が OK → DataPreview へ遷移する", async () => {
      mockApi.createCorrelationTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "corr_result" },
      });
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      // テーブルを選択
      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      // 出力データ名を入力
      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(mockApi.createCorrelationTable).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → エラーダイアログを表示する", async () => {
      mockApi.createCorrelationTable.mockResolvedValue({
        code: "UNEXPECTED_ERROR",
        message: "相関計算に失敗しました",
      });
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "Error.UnexpectedError",
        );
      });
    });

    it("APIがthrowした場合 → extractApiErrorMessage経由でダイアログを表示する", async () => {
      mockApi.createCorrelationTable.mockRejectedValue(
        new Error("ネットワークエラー"),
      );
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ネットワークエラー",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      useCurrentPageStore.setState({ currentView: "CorrelationMatrix" });
      render(<CorrelationMatrix />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
