import { getEconomiconAppAPI } from "@/api/endpoints";
import { LogitRegressionForm } from "@/components/organisms/Form/LogitRegressionForm";
import { ProbitRegressionForm } from "@/components/organisms/Form/ProbitRegressionForm";
import { showMessageDialog } from "@/lib/dialog/message";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

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

const REGRESSION_RESULT = {
  resultId: "r-001",
};

const ANALYSIS_DETAIL = {
  id: "r-001",
  name: "Binary Choice 1",
  description: "desc",
  tableName: "sales",
  resultType: "regression",
  createdAt: "2026-04-29T10:15:30Z",
  modelPath: null,
  modelType: "logit",
  entityIdColumn: null,
  timeColumn: null,
  resultData: {
    tableName: "sales",
    dependentVariable: "price",
    explanatoryVariables: ["quantity"],
    regressionResult: "Logit",
    parameters: [],
    modelStatistics: {
      nObservations: 100,
      pseudoRSquared: 0.2,
      logLikelihood: -12.3,
    },
  },
};

const mockApi = {
  regression: vi.fn(),
  getAnalysisResult: vi.fn(),
};

const onCancel = vi.fn();

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
  useCurrentPageStore.setState({ currentView: "Workspace" });
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

describe("BinaryChoiceRegressionForm", () => {
  it("Logit 画面は平均限界効果チェックが初期状態で有効", () => {
    render(<LogitRegressionForm onCancel={onCancel} />);

    expect(screen.getByText("LogitRegressionForm.Title")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: /LinearRegressionForm.AdvancedOptions/,
      }),
    );
    expect(
      screen.getByTestId("calculate-marginal-effects-checkbox"),
    ).toBeChecked();
  });

  it.each([
    ["logit", LogitRegressionForm, "LogitRegressionForm.Title"],
    ["probit", ProbitRegressionForm, "ProbitRegressionForm.Title"],
  ] as const)(
    "%s の submit で analysis.method と calculateMarginalEffects を送る",
    async (method, Component, titleKey) => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<Component onCancel={onCancel} />);

      expect(screen.getByText(titleKey)).toBeInTheDocument();

      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByRole("button", { name: "add-variable" }));

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis: {
              method,
              calculateMarginalEffects: true,
            },
          }),
        );
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
    },
  );
});
