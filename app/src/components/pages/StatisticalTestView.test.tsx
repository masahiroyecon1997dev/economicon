import { getEconomiconAppAPI } from "@/api/endpoints";
import { StatisticalTestView } from "@/components/pages/StatisticalTestView";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      if (options?.number) {
        return `${key}:${options.number}`;
      }
      return key;
    },
  }),
}));

vi.mock("@/api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

vi.mock("@/lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("@/components/atoms/Input/Select", () => ({
  Select: ({
    value,
    onValueChange,
    children,
    disabled,
  }: {
    value: string;
    onValueChange: (value: string) => void;
    children: React.ReactNode;
    disabled?: boolean;
  }) => (
    <select
      value={value}
      disabled={disabled}
      onChange={(event) => onValueChange(event.target.value)}
    >
      <option value="">placeholder</option>
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

const mockGetColumnList = vi.fn();
const mockStatisticalTest = vi.fn();
const mockGetAnalysisResult = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  useCurrentPageStore.setState({ currentView: "StatisticalTestView" });
  useTableListStore.setState({ tableList: ["sales", "orders"] });
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [{ name: "value", type: "Float64" }],
        totalRows: 10,
        isActive: true,
      },
    ],
    activeTableName: "sales",
  });
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
    clearActiveResult: vi.fn(),
  });

  mockGetColumnList.mockResolvedValue({
    code: "OK",
    result: {
      columnInfoList: [{ name: "value", type: "Float64" }],
    },
  });
  mockStatisticalTest.mockResolvedValue({
    code: "OK",
    result: { resultId: "stat-test-id" },
  });
  mockGetAnalysisResult.mockResolvedValue({
    code: "OK",
    result: {
      id: "stat-test-id",
      name: "t-test（1群） #1",
      description: "",
      tableName: "sales",
      resultType: "statistical_test",
      resultData: {
        statistic: 2.3,
        pValue: 0.02,
        df: 10,
        confidenceInterval: { lower: 0.1, upper: 0.9 },
        confidenceLevel: 0.95,
        effectSize: 0.5,
      },
      createdAt: "2026-05-05T10:00:00Z",
      modelPath: null,
      modelType: null,
      entityIdColumn: null,
      timeColumn: null,
      summaryText: "statistical_test",
    },
  });

  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    getColumnList: mockGetColumnList,
    statisticalTest: mockStatisticalTest,
    getAnalysisResult: mockGetAnalysisResult,
  } as never);
});

describe("StatisticalTestView", () => {
  it("列未選択のまま送信するとエラーを表示する", async () => {
    render(<StatisticalTestView />);

    fireEvent.submit(document.querySelector("form")!);

    await waitFor(() => {
      expect(
        screen.getByText("StatisticalTestView.ErrorColumnRequired"),
      ).toBeInTheDocument();
    });
  });

  it("成功時は分析結果タブを開いて DataPreview に戻る", async () => {
    const user = userEvent.setup();
    render(<StatisticalTestView />);

    await waitFor(() => {
      expect(mockGetColumnList).toHaveBeenCalledWith({
        tableName: "sales",
        isNumberOnly: true,
      });
    });

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[2]!, "value");
    await user.click(screen.getByText("StatisticalTestView.RunTest"));

    await waitFor(() => {
      expect(mockStatisticalTest).toHaveBeenCalledWith(
        expect.objectContaining({
          testType: "t-test",
          samples: [{ tableName: "sales", columnName: "value" }],
        }),
      );
      expect(mockStatisticalTest).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe(
        "result:stat-test-id",
      );
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
