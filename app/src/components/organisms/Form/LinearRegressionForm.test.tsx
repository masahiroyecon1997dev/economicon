import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAPI } from "../../../api/endpoints";
import { showMessageDialog } from "../../../lib/dialog/message";
import { useRegressionResultsStore } from "../../../stores/regressionResults";
import { useTableListStore } from "../../../stores/tableList";
import { LinearRegressionForm } from "./LinearRegressionForm";

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

// VariableSelectorField は表示が複雑なのでスタブ化
vi.mock("../../molecules/Field/VariableSelectorField", () => ({
  VariableSelectorField: ({
    label,
    onAdd,
  }: {
    label: string;
    selected: string[];
    onAdd: (v: string) => void;
    onRemove: (v: string) => void;
    options: { value: string; label: string }[];
  }) => (
    <div>
      <span>{label}</span>
      <button type="button" onClick={() => onAdd("price")}>
        add-variable
      </button>
    </div>
  ),
}));

vi.mock("../../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({
    selectedTableName: "sales",
    setSelectedTableName: vi.fn(),
    columnList: [
      { name: "price", type: "Float64" },
      { name: "quantity", type: "Int64" },
    ],
    setColumnList: vi.fn(),
  }),
}));

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------
const REGRESSION_RESULT = {
  resultId: "r-001",
};

const ANALYSIS_DETAIL = {
  regressionOutput: {
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
  vi.mocked(getEconomiconAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
  useRegressionResultsStore.setState({ results: [] });
});

describe("LinearRegressionForm", () => {
  describe("バリデーション", () => {
    it("テーブル未選択でサブミット → DataNameSelectエラーが表示される", async () => {
      // useTableColumnLoader を「selectedTableName = ''」でオーバーライド
      vi.doMock("../../../hooks/useTableColumnLoader", () => ({
        useTableColumnLoader: () => ({
          selectedTableName: "",
          setSelectedTableName: vi.fn(),
          columnList: [],
          setColumnList: vi.fn(),
        }),
      }));

      const user = userEvent.setup();
      render(<LinearRegressionForm onCancel={onCancel} />);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameSelect"),
        ).toBeInTheDocument();
      });
    });

    it("目的変数未選択でサブミット → DependentVariableRequiredエラーが表示される", async () => {
      const user = userEvent.setup();
      render(<LinearRegressionForm onCancel={onCancel} />);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DependentVariableRequired"),
        ).toBeInTheDocument();
      });
    });

    it("説明変数が0件でサブミット → ExplanatoryVariablesRequiredエラーが表示される", async () => {
      const user = userEvent.setup();
      render(
        <LinearRegressionForm
          onCancel={onCancel}
          onAnalysisComplete={onAnalysisComplete}
        />,
      );

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.ExplanatoryVariablesRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時（2段連鎖）", () => {
    it("regression → getAnalysisResult が両方成功すると addResult と onAnalysisComplete が呼ばれる", async () => {
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

      // 目的変数を設定（Field直接操作）
      const depSelect = screen.getByRole("combobox", {
        name: /DependentVariable|目的変数/i,
      });
      await user.click(depSelect);
      const depOption = await screen.findByRole("option", { name: "price" });
      await user.click(depOption);

      // 説明変数を追加（スタブボタン）
      const addBtn = screen.getByRole("button", { name: "add-variable" });
      await user.click(addBtn);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(onAnalysisComplete).toHaveBeenCalledWith(0);
      });
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
      expect(useRegressionResultsStore.getState().results).toHaveLength(1);
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

      // 目的変数・説明変数を設定
      const depSelect = screen.getByRole("combobox", {
        name: /DependentVariable|目的変数/i,
      });
      await user.click(depSelect);
      const depOption = await screen.findByRole("option", { name: "price" });
      await user.click(depOption);

      const addBtn = screen.getByRole("button", { name: "add-variable" });
      await user.click(addBtn);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

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

      const depSelect = screen.getByRole("combobox", {
        name: /DependentVariable|目的変数/i,
      });
      await user.click(depSelect);
      const depOption = await screen.findByRole("option", { name: "price" });
      await user.click(depOption);

      const addBtn = screen.getByRole("button", { name: "add-variable" });
      await user.click(addBtn);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

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

      const depSelect = screen.getByRole("combobox", {
        name: /DependentVariable|目的変数/i,
      });
      await user.click(depSelect);
      const depOption = await screen.findByRole("option", { name: "price" });
      await user.click(depOption);

      const addBtn = screen.getByRole("button", { name: "add-variable" });
      await user.click(addBtn);

      const submitBtn = screen.getByRole("button", { name: /実行|Execute/i });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "接続タイムアウト",
        );
      });
    });
  });
});
