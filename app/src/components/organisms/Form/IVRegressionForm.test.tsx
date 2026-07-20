import { getEconomiconAppAPI } from "@/api/endpoints";
import { IVRegressionForm } from "@/components/organisms/Form/IVRegressionForm";
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
    t: (key: string, opts?: Record<string, unknown>) => {
      if (!opts) return key;
      return Object.entries(opts).reduce(
        (s, [k, v]) => s.replace(`{{${k}}}`, String(v)),
        key,
      );
    },
  }),
}));

vi.mock("../../../api/endpoints");
vi.mock("../../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

// SearchableSelect: 選択肢をボタンで操作できるシンプルなスタブ
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

// VariableSelectorField: name prop を data-testid に使って3セレクターを区別する
vi.mock("../../molecules/Field/VariableSelectorField", () => ({
  VariableSelectorField: ({
    label,
    name,
    mode,
    selectedValues = [],
    onSingleChange,
    onMultipleChange,
    error,
  }: {
    label: string;
    name?: string;
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
        data-testid={name ? `add-${name}` : "add-variable"}
        onClick={() => {
          if (mode === "single") {
            onSingleChange?.("quantity");
          } else {
            onMultipleChange?.([...selectedValues, "quantity"]);
          }
        }}
      >
        add-variable
      </button>
    </div>
  ),
}));

// Select/SelectItem: ネイティブ select/option としてスタブ化（ivMethod 等の操作を可能にする）
vi.mock("../../atoms/Input/Select", () => ({
  Select: ({
    id,
    value,
    onValueChange,
    children,
    disabled,
  }: {
    id?: string;
    value: string;
    onValueChange: (value: string) => void;
    children: React.ReactNode;
    disabled?: boolean;
  }) => (
    <select
      id={id}
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      disabled={disabled}
    >
      {children}
    </select>
  ),
  SelectItem: ({
    value,
    children,
  }: {
    value: string;
    children: React.ReactNode;
  }) => <option value={value}>{children}</option>,
}));

// AnalysisOptionsCard: 常に children を表示（open/close 状態を気にしない）
vi.mock("../../molecules/Card/AnalysisOptionsCard", () => ({
  AnalysisOptionsCard: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="options-card">{children}</div>
  ),
}));

// useTableColumnLoader をテストごとに制御可能なミュータブル状態で定義
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
// Fixtures
// ---------------------------------------------------------------------------
const REGRESSION_RESULT = {
  resultId: "r-001",
};

const ANALYSIS_DETAIL = {
  id: "r-001",
  name: "IV 1",
  description: "desc",
  tableName: "sales",
  resultType: "regression",
  createdAt: "2026-07-20T10:00:00Z",
  modelPath: null,
  modelType: "iv",
  entityIdColumn: null,
  timeColumn: null,
  resultData: {
    tableName: "sales",
    dependentVariable: "price",
    explanatoryVariables: [],
    regressionResult: "IV",
    parameters: [
      {
        variable: "quantity",
        coefficient: 2.0,
        standardError: 0.15,
        pValue: 0.001,
        tValue: 13.3,
        confidenceIntervalLower: 1.7,
        confidenceIntervalUpper: 2.3,
      },
    ],
    modelStatistics: {
      nObservations: 100,
      R2: 0.72,
      adjustedR2: 0.715,
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

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("IVRegressionForm", () => {
  it("タイトルと説明を表示する", () => {
    render(<IVRegressionForm onCancel={onCancel} />);

    expect(screen.getByText("IVRegressionForm.Title")).toBeInTheDocument();
    expect(
      screen.getByText("IVRegressionForm.Description"),
    ).toBeInTheDocument();
  });

  // =========================================================================
  // バリデーション
  // =========================================================================
  describe("バリデーション", () => {
    it("テーブル未選択でサブミット → DataNameSelect エラーが表示される", async () => {
      mockTableLoader.selectedTableName = "";
      mockTableLoader.columnList = [];

      render(<IVRegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameSelect"),
        ).toBeInTheDocument();
      });
    });

    it("被説明変数未選択でサブミット → DependentVariableRequired エラーが表示される", async () => {
      render(<IVRegressionForm onCancel={onCancel} />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DependentVariableRequired"),
        ).toBeInTheDocument();
      });
    });

    it("内生変数0件でサブミット → EndogenousVariablesRequired エラーが表示される", async () => {
      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // 被説明変数を設定
      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));

      // 操作変数だけ設定（内生変数は未設定）
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.EndogenousVariablesRequired"),
        ).toBeInTheDocument();
      });
    });

    it("操作変数0件でサブミット → InstrumentalVariablesRequired エラーが表示される", async () => {
      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // 被説明変数を設定
      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));

      // 内生変数だけ設定（操作変数は未設定）
      await user.click(screen.getByTestId("add-endogenousVariables"));

      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.InstrumentalVariablesRequired"),
        ).toBeInTheDocument();
      });
    });

    it("説明変数0件でもエラーにならない（IV では外生変数は省略可）", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // 被説明変数を設定
      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));

      // 説明変数はクリックしない
      // 内生変数・操作変数のみ設定
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            explanatoryVariables: [],
            analysis: expect.objectContaining({ method: "iv" }),
          }),
        );
      });
      expect(
        screen.queryByText("ValidationMessages.ExplanatoryVariablesRequired"),
      ).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // API 成功時
  // =========================================================================
  describe("API 成功時（2段連鎖）", () => {
    it("regression→getAnalysisResult が両方成功すると結果タブが開く", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // 被説明変数を設定
      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));

      // 説明変数・内生変数・操作変数を設定
      await user.click(screen.getByTestId("add-explanatoryVariables"));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(mockApi.getAnalysisResult).toHaveBeenCalledWith("r-001");
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe("result:r-001");
    });

    it("regression API に method='iv' を含むリクエストを送信する", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis: expect.objectContaining({
              method: "iv",
              ivMethod: "2sls",
              endogenousVariables: ["quantity"],
              instrumentalVariables: ["quantity"],
            }),
          }),
        );
      });
    });
  });

  // =========================================================================
  // API 失敗時
  // =========================================================================
  describe("API 失敗時", () => {
    it("regression が code ≠ OK → ダイアログにメッセージが表示される（getAnalysisResult は呼ばれない）", async () => {
      mockApi.regression.mockResolvedValue({
        code: "INVALID_TABLE",
        message: "テーブルが見つかりません",
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "テーブルが見つかりません",
        );
      });
      expect(mockApi.getAnalysisResult).not.toHaveBeenCalled();
    });

    it("getAnalysisResult が code ≠ OK → ダイアログにメッセージが表示される", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "RESULT_NOT_FOUND",
        message: "結果が見つかりません",
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "結果が見つかりません",
        );
      });
    });

    it("regression が throw した場合 → エラーメッセージダイアログが表示される", async () => {
      mockApi.regression.mockRejectedValue(new Error("接続タイムアウト"));

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "接続タイムアウト",
        );
      });
    });
  });

  // =========================================================================
  // GMM オプション（条件付きレンダリング）
  // =========================================================================
  describe("GMM オプション", () => {
    it("ivMethod=2sls（デフォルト）のとき GmmWeightMatrixLabel は表示されない", () => {
      render(<IVRegressionForm onCancel={onCancel} />);

      expect(
        screen.queryByText("IVRegressionForm.GmmWeightMatrixLabel"),
      ).not.toBeInTheDocument();
    });

    it("ivMethod を gmm に変更すると GmmWeightMatrixLabel が表示される", async () => {
      render(<IVRegressionForm onCancel={onCancel} />);

      // デフォルトは 2SLS → GMM フィールドなし
      expect(
        screen.queryByText("IVRegressionForm.GmmWeightMatrixLabel"),
      ).not.toBeInTheDocument();

      // ivMethod Select を GMM に変更
      const ivMethodSelect = screen.getByLabelText(
        "IVRegressionForm.IvMethodLabel",
      );
      fireEvent.change(ivMethodSelect, { target: { value: "gmm" } });

      // GMM 重み行列フィールドが表示されること
      await waitFor(() => {
        expect(
          screen.getByText("IVRegressionForm.GmmWeightMatrixLabel"),
        ).toBeInTheDocument();
      });
    });

    it("ivMethod=gmm で regression に gmmWeightMatrix が送信される", async () => {
      mockApi.regression.mockResolvedValue({
        code: "OK",
        result: REGRESSION_RESULT,
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: ANALYSIS_DETAIL,
      });

      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // GMM に変更
      const ivMethodSelect = screen.getByLabelText(
        "IVRegressionForm.IvMethodLabel",
      );
      fireEvent.change(ivMethodSelect, { target: { value: "gmm" } });

      // 変数設定
      await user.click(
        screen.getByLabelText("LinearRegressionForm.DependentVariable"),
      );
      await user.click(await screen.findByRole("option", { name: "price" }));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      await submitForm();

      await waitFor(() => {
        expect(mockApi.regression).toHaveBeenCalledWith(
          expect.objectContaining({
            analysis: expect.objectContaining({
              method: "iv",
              ivMethod: "gmm",
              gmmWeightMatrix: "robust",
            }),
          }),
        );
      });
    });
  });

  // =========================================================================
  // 識別条件バッジ
  // =========================================================================
  describe("識別条件バッジ", () => {
    it("内生変数が0件のときバッジは表示されない", () => {
      render(<IVRegressionForm onCancel={onCancel} />);

      expect(
        screen.queryByText(/IVRegressionForm\.IdentificationStatus/),
      ).not.toBeInTheDocument();
    });

    it("内生1件・操作1件のとき識別条件バッジが緑色で表示される", async () => {
      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      const badge = screen.getByText(/IVRegressionForm\.IdentificationStatus/);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass("text-green-600");
    });

    it("内生2件・操作1件のとき識別不足で琥珀色バッジが表示される", async () => {
      const user = userEvent.setup();
      render(<IVRegressionForm onCancel={onCancel} />);

      // 内生変数を2件追加（同じボタンを2回クリック → ["quantity", "quantity"]）
      await user.click(screen.getByTestId("add-endogenousVariables"));
      await user.click(screen.getByTestId("add-endogenousVariables"));
      // 操作変数を1件追加
      await user.click(screen.getByTestId("add-instrumentalVariables"));

      const badge = screen.getByText(/IVRegressionForm\.IdentificationStatus/);
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass("text-amber-600");
    });
  });
});
