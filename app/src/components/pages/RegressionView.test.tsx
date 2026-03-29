import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useRegressionResultsStore } from "../../stores/regressionResults";
import type { LinearRegressionResultType } from "../../types/commonTypes";
import { Regression } from "./RegressionView";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string | number>) => {
      if (!opts) return key;
      return Object.entries(opts).reduce(
        (s, [k, v]) => s.replace(`{{${k}}}`, String(v)),
        key,
      );
    },
  }),
}));

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

// 子コンポーネントのスタブ化（重量コンポーネント）
vi.mock("../organisms/Form/LinearRegressionForm", () => ({
  LinearRegressionForm: ({
    onCancel,
    onAnalysisComplete,
  }: {
    onCancel: () => void;
    onAnalysisComplete: (idx: number) => void;
  }) => (
    <div>
      <div data-testid="regression-form">LinearRegressionForm</div>
      <button type="button" onClick={onCancel}>
        CancelInForm
      </button>
      <button
        type="button"
        onClick={() => onAnalysisComplete(0)}
        data-testid="complete-analysis"
      >
        CompleteAnalysis
      </button>
    </div>
  ),
}));

vi.mock("../organisms/Result/RegressionResult", () => ({
  RegressionResult: ({ result }: { result: { resultId: string } }) => (
    <div data-testid={`regression-result-${result.resultId}`} />
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  deleteAnalysisResult: vi.fn(),
};

const MOCK_RESULT: LinearRegressionResultType = {
  resultId: "result-1",
  tableName: "sales",
  dependentVariable: "price",
  explanatoryVariables: ["quantity"],
  regressionResult: "OLS",
  parameters: [
    {
      variable: "quantity",
      coefficient: 1.5,
      standardError: 0.12,
      pValue: 0.001,
      tValue: 12.5,
      confidenceIntervalLower: 1.26,
      confidenceIntervalUpper: 1.74,
    },
  ],
  modelStatistics: {
    nObservations: 10,
    R2: 0.9,
    adjustedR2: 0.85,
    fValue: 50,
    fProbability: 0.001,
  },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useRegressionResultsStore.setState({ results: [] });
  useCurrentPageStore.setState({ currentView: "LinearRegressionForm" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("RegressionView コンポーネント", () => {
  describe("初期表示", () => {
    it("分析設定タブが表示される", () => {
      render(<Regression />);
      expect(screen.getByText("RegressionTab.FormTab")).toBeInTheDocument();
    });

    it("分析設定フォームがデフォルトで表示される", () => {
      render(<Regression />);
      expect(screen.getByTestId("regression-form")).toBeInTheDocument();
    });

    it("結果がない場合は結果タブが表示されない", () => {
      render(<Regression />);
      expect(screen.queryByText(/RegressionTab.ResultLabel/)).toBeNull();
    });
  });

  describe("結果タブ", () => {
    it("結果がある場合は結果タブが表示される", () => {
      useRegressionResultsStore.setState({ results: [MOCK_RESULT] });
      render(<Regression />);

      expect(
        screen.getAllByRole("button", { name: "RegressionTab.DeleteResult" }),
      ).toHaveLength(1);
    });

    it("複数結果がある場合は対応するタブ数表示される", () => {
      useRegressionResultsStore.setState({
        results: [MOCK_RESULT, { ...MOCK_RESULT, resultId: "result-2" }],
      });
      render(<Regression />);

      expect(
        screen.getAllByRole("button", { name: "RegressionTab.DeleteResult" }),
      ).toHaveLength(2);
    });

    it("分析完了コールバックで結果タブに切り替わる", async () => {
      useRegressionResultsStore.setState({ results: [MOCK_RESULT] });
      const user = userEvent.setup();
      render(<Regression />);

      // 分析完了ボタンをクリック
      await user.click(screen.getByTestId("complete-analysis"));

      await waitFor(() => {
        expect(
          screen.getByTestId("regression-result-result-1"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("結果の削除", () => {
    it("結果タブの×ボタンをクリックすると deleteAnalysisResult が呼ばれる", async () => {
      mockApi.deleteAnalysisResult.mockResolvedValue({ code: "OK" });
      useRegressionResultsStore.setState({ results: [MOCK_RESULT] });
      const user = userEvent.setup();
      render(<Regression />);

      const deleteBtn = screen.getByRole("button", {
        name: "RegressionTab.DeleteResult",
      });
      await user.click(deleteBtn);

      await waitFor(() => {
        expect(mockApi.deleteAnalysisResult).toHaveBeenCalledWith("result-1");
      });
      expect(useRegressionResultsStore.getState().results).toHaveLength(0);
    });

    it("deleteAnalysisResult がthrowした場合 → エラーダイアログを表示して結果を削除しない", async () => {
      mockApi.deleteAnalysisResult.mockRejectedValue(new Error("削除失敗"));
      useRegressionResultsStore.setState({ results: [MOCK_RESULT] });
      const user = userEvent.setup();
      render(<Regression />);

      const deleteBtn = screen.getByRole("button", {
        name: "RegressionTab.DeleteResult",
      });
      await user.click(deleteBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "削除失敗",
        );
      });
      // 結果は削除されない
      expect(useRegressionResultsStore.getState().results).toHaveLength(1);
    });
  });

  describe("キャンセル", () => {
    it("フォーム内のキャンセルボタンで DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<Regression />);

      await user.click(screen.getByText("CancelInForm"));

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
