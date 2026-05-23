import { getEconomiconAppAPI } from "@/api/endpoints";
import { StatisticalTestView } from "@/components/pages/StatisticalTestView";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockT = (key: string, options?: Record<string, unknown>) => {
  if (options?.number) {
    return `${key}:${options.number}`;
  }
  return key;
};

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: mockT,
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
  useCurrentPageStore.setState({ currentView: "Workspace" });
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
  it("テーブルが 0 件の場合 NoTables state を表示し、ImportDataFile に遷移できる", async () => {
    const user = userEvent.setup();
    useTableListStore.setState({ tableList: [] });

    render(<StatisticalTestView />);

    expect(screen.getByTestId("analysis-no-tables-state")).toBeInTheDocument();

    await user.click(
      screen.getByRole("button", {
        name: "AnalysisEmptyState.NoTablesAction",
      }),
    );

    expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
  });

  it("対象列がないサンプルでは共通 no-columns state を表示する", async () => {
    mockGetColumnList.mockResolvedValue({
      code: "OK",
      result: {
        columnInfoList: [],
      },
    });

    render(<StatisticalTestView />);

    expect(
      await screen.findByTestId("statistical-test-no-columns-state-0"),
    ).toBeInTheDocument();
  });

  it("列未選択のまま送信するとエラーを表示する", async () => {
    render(<StatisticalTestView />);

    fireEvent.submit(document.querySelector("form")!);

    await waitFor(() => {
      expect(
        screen.getByText("StatisticalTestView.ErrorColumnRequired"),
      ).toBeInTheDocument();
    });
  });

  it("成功時に結果タブを開いて Workspace に戻る", async () => {
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
    fireEvent.submit(document.querySelector("form")!);

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
      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
    });
  });
});
