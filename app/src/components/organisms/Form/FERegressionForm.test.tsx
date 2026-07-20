import { getEconomiconAppAPI } from "@/api/endpoints";
import { FERegressionForm } from "@/components/organisms/Form/FERegressionForm";
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
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

/** FormField の label → SearchableSelect の親 div → within でオプションを選択する */
const clickOptionInField = async (
  user: ReturnType<typeof userEvent.setup>,
  labelText: string,
  optionName: string,
) => {
  const trigger = screen.getByLabelText(labelText);
  await user.click(
    within(trigger.parentElement!).getByRole("option", { name: optionName }),
  );
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

vi.mock("../../atoms/Input/SearchableSelect", () => ({
  SearchableSelect: ({
    id,
    value,
    onValueChange,
    options,
    placeholder,
    disabled,
  }: {
    id?: string;
    value: string;
    onValueChange: (value: string) => void;
    options: Array<{ value: string; label: string }>;
    placeholder?: string;
    disabled?: boolean;
  }) => (
    <div>
      <button id={id} type="button" disabled={disabled}>
        {value || placeholder || "select"}
      </button>
      <div role="listbox">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            role="option"
            aria-selected={option.value === value}
            onClick={() => onValueChange(option.value)}
            disabled={disabled}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  ),
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
            onSingleChange?.("x1");
          } else {
            onMultipleChange?.([...selectedValues, "x1"]);
          }
        }}
      >
        add-variable
      </button>
    </div>
  ),
}));

const mockTableLoader = vi.hoisted(() => ({
  selectedTableName: "panel_data",
  setSelectedTableName: vi.fn(),
  columnList: [
    { name: "y", type: "Float64" },
    { name: "x1", type: "Float64" },
    { name: "x2", type: "Float64" },
    { name: "entity_id", type: "Float64" },
    { name: "time_id", type: "Float64" },
  ],
  setColumnList: vi.fn(),
}));

vi.mock("../../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({ ...mockTableLoader }),
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const FE_REGRESSION_RESULT = { resultId: "fe-r-001" };

const FE_ANALYSIS_DETAIL = {
  id: "fe-r-001",
  name: "FE 1",
  description: "",
  tableName: "panel_data",
  resultType: "regression",
  createdAt: "2026-07-20T10:00:00Z",
  modelPath: null,
  modelType: "fe",
  entityIdColumn: "entity_id",
  timeColumn: "time_id",
  resultData: {
    tableName: "panel_data",
    dependentVariable: "y",
    explanatoryVariables: ["x1", "x2"],
    regressionResult: "Fixed Effects (Within)",
    parameters: [
      {
        variable: "x1",
        coefficient: 3.0,
        standardError: 0.036,
        pValue: 0.0,
        tValue: 82.7,
        confidenceIntervalLower: 2.93,
        confidenceIntervalUpper: 3.07,
      },
      {
        variable: "x2",
        coefficient: -2.05,
        standardError: 0.045,
        pValue: 0.0,
        tValue: -45.0,
        confidenceIntervalLower: -2.14,
        confidenceIntervalUpper: -1.96,
      },
    ],
    modelStatistics: {
      nObservations: 100,
      nEntities: 10,
      R2Within: 0.9897,
      R2Between: 0.1215,
      R2Overall: 0.8195,
      fValue: 4246.4,
      fProbability: 0.0,
      fPooled: { statistic: 87.2, pValue: 0.0 },
    },
  },
};

const mockApi = {
  regression: vi.fn(),
  getAnalysisResult: vi.fn(),
};

const onCancel = vi.fn();

// ---------------------------------------------------------------------------
// beforeEach
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(mockTableLoader, {
    selectedTableName: "panel_data",
    setSelectedTableName: vi.fn(),
    columnList: [
      { name: "y", type: "Float64" },
      { name: "x1", type: "Float64" },
      { name: "x2", type: "Float64" },
      { name: "entity_id", type: "Float64" },
      { name: "time_id", type: "Float64" },
    ],
    setColumnList: vi.fn(),
  });
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["panel_data"] });
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("FERegressionForm", () => {
  it("タイトルと説明を表示する", () => {
    render(<FERegressionForm onCancel={onCancel} />);

    expect(screen.getByText("FERegressionForm.Title")).toBeInTheDocument();
    expect(
      screen.getByText("FERegressionForm.Description"),
    ).toBeInTheDocument();
  });

  // =========================================================================
  describe("バリデーション", () => {
    it("テーブル未選択でサブミット → DataNameSelectエラーが表示される", async () => {
      mockTableLoader.selectedTableName = "";
      mockTableLoader.columnList = [];

      render(<FERegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameSelect"),
        ).toBeInTheDocument();
      });
    });

    it("被説明変数未選択でサブミット → DependentVariableRequiredエラーが表示される", async () => {
      render(<FERegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DependentVariableRequired"),
        ).toBeInTheDocument();
      });
    });

    it("entityIdColumn未選択でサブミット → EntityIdColumnRequiredエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      // 被説明変数のみ選択し entityIdColumn は選ばない
      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));

      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.EntityIdColumnRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  describe("API成功時", () => {
    it("timeColumn未指定のとき regression に timeColumn:null を渡し結果タブを開く", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: FE_REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: FE_ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));
      await clickOptionInField(
        user,
        "FERegressionForm.EntityIdColumn",
        "entity_id",
      );
      // timeColumn は選択しない（デフォルト "" → null）

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis: expect.objectContaining({
              method: "fe",
              entityIdColumn: "entity_id",
              timeColumn: null,
            }),
          }),
        );
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe(
        "result:fe-r-001",
      );
    });

    it("timeColumn指定のとき regression に正しい timeColumn 値を渡す", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: FE_REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: FE_ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));
      await clickOptionInField(
        user,
        "FERegressionForm.EntityIdColumn",
        "entity_id",
      );
      await clickOptionInField(user, "FERegressionForm.TimeColumn", "time_id");

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis: expect.objectContaining({
              method: "fe",
              entityIdColumn: "entity_id",
              timeColumn: "time_id",
            }),
          }),
        );
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
    });
  });

  // =========================================================================
  describe("API失敗時", () => {
    it("regression が code ≠ OK → showMessageDialog が呼ばれ getAnalysisResult は呼ばれない", async () => {
      mockApi.regression.mockResolvedValue({
        code: "INVALID_TABLE",
        message: "テーブルが見つかりません",
      });

      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));
      await clickOptionInField(
        user,
        "FERegressionForm.EntityIdColumn",
        "entity_id",
      );

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "テーブルが見つかりません",
        );
      });
      expect(mockApi.getAnalysisResult).not.toHaveBeenCalled();
    });

    it("getAnalysisResult が code ≠ OK → showMessageDialog が呼ばれる", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: FE_REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "RESULT_NOT_FOUND",
        message: "結果が見つかりません",
      });

      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));
      await clickOptionInField(
        user,
        "FERegressionForm.EntityIdColumn",
        "entity_id",
      );

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "結果が見つかりません",
        );
      });
    });

    it("regression が throw したとき → showMessageDialog が呼ばれる", async () => {
      mockApi.regression.mockRejectedValue(new Error("接続タイムアウト"));

      const user = userEvent.setup();
      render(<FERegressionForm onCancel={onCancel} />);

      await clickOptionInField(
        user,
        "LinearRegressionForm.DependentVariable",
        "y",
      );
      await user.click(screen.getByRole("button", { name: "add-variable" }));
      await clickOptionInField(
        user,
        "FERegressionForm.EntityIdColumn",
        "entity_id",
      );

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
