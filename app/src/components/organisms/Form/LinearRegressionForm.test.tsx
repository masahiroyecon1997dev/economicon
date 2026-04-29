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
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { LinearRegressionForm } from "@/components/organisms/Form/LinearRegressionForm";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
/** type="submit" ボタンは JSDOM で form の submit イベントを発火しないため直接 fireEvent.submit を使う */
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

vi.mock("../../../api/endpoints");
vi.mock("../../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

// VariableSelectorField はスタブ化（error prop も表示し、single/multiple を mode で切り替える）
vi.mock("../../molecules/Field/VariableSelectorField", () => ({
  VariableSelectorField: ({
    label,
    mode,
    selectedValues = [],
    onSingleChange,
    onMultipleChange,
    error,
  }: {
    label: string;
    mode: "single" | "multiple";
    selectedValues?: string[];
    selectedValue?: string;
    onSingleChange?: (value: string) => void;
    onMultipleChange?: (values: string[]) => void;
    error?: string;
  }) => (
    <div>
      <span>{label}</span>
      {error && <p role="alert">{error}</p>}
      <button
        type="button"
        onClick={() => {
          if (mode === "single") {
            onSingleChange?.("price");
          } else {
            onMultipleChange?.([...selectedValues, "price"]);
          }
        }}
      >
        add-variable
      </button>
    </div>
  ),
}));

// テストごとに selectedTableName を変えられるよう vi.hoisted でミュータブルな状態を作る
const mockTableLoader = vi.hoisted(() => ({
  selectedTableName: "sales",
  setSelectedTableName: vi.fn(),
  columnList: [
    { name: "price", type: "Float64" },
    { name: "quantity", type: "Int64" },
  ],
  setColumnList: vi.fn(),
}));

vi.mock("../../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({ ...mockTableLoader }),
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const REGRESSION_RESULT = {
  resultId: "r-001",
};

const ANALYSIS_DETAIL = {
  id: "r-001",
  name: "OLS 1",
  description: "desc",
  tableName: "sales",
  resultType: "regression",
  createdAt: "2026-04-29T10:15:30Z",
  modelPath: null,
  modelType: "ols",
  entityIdColumn: null,
  timeColumn: null,
  resultData: {
    tableName: "sales",
    dependentVariable: "price",
    explanatoryVariables: ["quantity"],
    regressionResult: "OLS",
    parameters: [
      {
        variable: "quantity",
        coefficient: 1.5,
        standardError: 0.1,
        pValue: 0.001,
        tValue: 15.0,
        confidenceIntervalLower: 1.3,
        confidenceIntervalUpper: 1.7,
      },
    ],
    modelStatistics: {
      nObservations: 100,
      R2: 0.85,
      adjustedR2: 0.849,
      fValue: 567.3,
      fProbability: 0.0,
    },
  },
};

const mockApi = {
  regression: vi.fn(),
  getAnalysisResult: vi.fn(),
};

const onCancel = vi.fn();
const onAnalysisComplete = vi.fn();

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(mockTableLoader, {
    selectedTableName: "sales",
    setSelectedTableName: vi.fn(),
    columnList: [
      { name: "price", type: "Float64" },
      { name: "quantity", type: "Int64" },
    ],
    setColumnList: vi.fn(),
  });
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
  useCurrentPageStore.setState({ currentView: "LinearRegressionForm" });
  useWorkspaceTabsStore.setState({ tabs: [], activeTabId: null });
  useAnalysisResultsStore.setState({
    pane: "data",
    summaries: [],
    activeResultId: null,
    activeResultDetail: null,
    isListLoading: false,
    isDetailLoading: false,
    setPane: useAnalysisResultsStore.getState().setPane,
    setActiveResult: useAnalysisResultsStore.getState().setActiveResult,
    fetchSummaries: vi.fn().mockResolvedValue(undefined),
    openResult: vi.fn(),
    removeSummary: vi.fn(),
    upsertSummary: vi.fn(),
    clearActiveResult: useAnalysisResultsStore.getState().clearActiveResult,
  });
});

describe("LinearRegressionForm", () => {
  describe("バリデーション", () => {
    it("テーブル未選択でサブミット → DataNameSelectエラーが表示される", async () => {
      mockTableLoader.selectedTableName = "";
      mockTableLoader.columnList = [];

      render(<LinearRegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameSelect"),
        ).toBeInTheDocument();
      });
    });

    it("目的変数未選択でサブミット → DependentVariableRequiredエラーが表示される", async () => {
      render(<LinearRegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DependentVariableRequired"),
        ).toBeInTheDocument();
      });
    });

    it("説明変数が0件でサブミット → ExplanatoryVariablesRequiredエラーが表示される", async () => {
      render(
        <LinearRegressionForm
          onCancel={onCancel}
          onAnalysisComplete={onAnalysisComplete}
        />,
      );

      // 目的変数のみ設定して説明変数は空のまま
      const [depAddBtn] = screen.getAllByRole("button", {
        name: "add-variable",
      });
      await userEvent.setup().click(depAddBtn);

      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.ExplanatoryVariablesRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時（2段連鎖）", () => {
    it("regression → getAnalysisResult が両方成功すると共通タブを開いて DataPreview に戻る", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(
        <LinearRegressionForm
          onCancel={onCancel}
          onAnalysisComplete={onAnalysisComplete}
        />,
      );

      const [depAddBtn, expAddBtn] = screen.getAllByRole("button", {
        name: "add-variable",
      });
      await user.click(depAddBtn);
      await user.click(expAddBtn);

      await submitForm();

      await waitFor(() => {
        expect(onAnalysisComplete).toHaveBeenCalledWith(0);
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe("result:r-001");
    });
  });

  describe("API失敗時", () => {
    it("regression が code ≠ OK → ダイアログにAPIのmessageが表示される（getAnalysisResultは呼ばれない）", async () => {
      mockApi.regression.mockResolvedValue({
        code: "INVALID_TABLE",
        message: "テーブルが見つかりません",
      });

      const user = userEvent.setup();
      render(<LinearRegressionForm onCancel={onCancel} />);

      const [depAddBtn, expAddBtn] = screen.getAllByRole("button", {
        name: "add-variable",
      });
      await user.click(depAddBtn);
      await user.click(expAddBtn);

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "テーブルが見つかりません",
        );
      });
      expect(mockApi.getAnalysisResult).not.toHaveBeenCalled();
    });

    it("getAnalysisResult が code ≠ OK → ダイアログにAPIのmessageが表示される", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "RESULT_NOT_FOUND",
        message: "結果が見つかりません",
      });

      const user = userEvent.setup();
      render(<LinearRegressionForm onCancel={onCancel} />);

      const [depAddBtn, expAddBtn] = screen.getAllByRole("button", {
        name: "add-variable",
      });
      await user.click(depAddBtn);
      await user.click(expAddBtn);

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "結果が見つかりません",
        );
      });
    });

    it("regression がthrowした場合 → extractApiErrorMessage経由でダイアログを表示する", async () => {
      mockApi.regression.mockRejectedValue(new Error("接続タイムアウト"));

      const user = userEvent.setup();
      render(<LinearRegressionForm onCancel={onCancel} />);

      const [depAddBtn, expAddBtn] = screen.getAllByRole("button", {
        name: "add-variable",
      });
      await user.click(depAddBtn);
      await user.click(expAddBtn);

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "接続タイムアウト",
        );
      });
    });
  });
});
