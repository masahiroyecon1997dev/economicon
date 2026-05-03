import { getEconomiconAppAPI } from "@/api/endpoints";
import { LeftSideMenu } from "@/components/pages/LeftSideMenu";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { showMessageDialog } from "@/lib/dialog/message";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string | number>) => {
      if (!opts) return key;
      return Object.entries(opts).reduce(
        (text, [name, value]) => text.replace(`{{${name}}}`, String(value)),
        key,
      );
    },
  }),
}));

vi.mock("../../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../lib/dialog/confirm", () => ({
  showConfirmDialog: vi.fn().mockResolvedValue(true),
}));

vi.mock("../../lib/utils/internal", () => ({
  getTableInfo: vi.fn().mockResolvedValue({
    tableName: "new_table",
    columnList: [{ name: "id", type: "Int64" }],
    totalRows: 0,
    isActive: true,
  }),
}));

// TableNav は外部依存コンポーネントだが、実体をテストするため未スタブ化
// ただし内部でapiを呼ぶ可能性があるためスタブ化する
vi.mock("../molecules/List/TableNav", () => ({
  TableNav: ({
    onTableClick,
  }: {
    activeTableName: string | null;
    onTableClick: (name: string) => void;
  }) => (
    <ul>
      <li>
        <button type="button" onClick={() => onTableClick("sales")}>
          sales
        </button>
      </li>
      <li>
        <button type="button" onClick={() => onTableClick("new_table")}>
          new_table
        </button>
      </li>
    </ul>
  ),
}));

vi.mock("../organisms/Dialog/OutputResultDialog", () => ({
  OutputResultDialog: ({ open }: { open: boolean }) =>
    open ? <div data-testid="output-result-dialog" /> : null,
}));

const mockApi = {
  deleteAnalysisResult: vi.fn(),
  getAnalysisResult: vi.fn(),
};

const MOCK_RESULT_DETAIL = {
  id: "result-1",
  name: "OLS 1",
  description: "desc",
  tableName: "sales",
  resultType: "regression",
  resultData: {
    tableName: "sales",
    dependentVariable: "price",
    explanatoryVariables: ["quantity"],
    regressionResult: "OLS",
    parameters: [],
    modelStatistics: { nObservations: 10 },
  },
  createdAt: "2026-04-29T10:15:30Z",
  modelPath: null,
  modelType: "ols",
  entityIdColumn: null,
  timeColumn: null,
};

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [{ name: "price", type: "Float64" }],
        totalRows: 10,
        isActive: false,
      },
    ],
    activeTableName: "sales",
  });
  useTableListStore.setState({ tableList: ["sales", "new_table"] });
  useCurrentPageStore.setState({ currentView: "ImportDataFile" });
  useWorkspaceTabsStore.setState({
    tabs: [],
    activeTabId: null,
  });
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
    openResult: vi.fn().mockResolvedValue(MOCK_RESULT_DETAIL),
    removeSummary: vi.fn(),
    upsertSummary: vi.fn(),
    clearActiveResult: vi.fn(),
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("LeftSideMenu コンポーネント", () => {
  it("初期表示ではデータタブが選択される", () => {
    render(<LeftSideMenu />);

    expect(screen.getByText("LeftSideMenu.Title")).toBeInTheDocument();
    expect(screen.getByTestId("left-menu-tab-data")).toBeInTheDocument();
    expect(screen.getByText("sales")).toBeInTheDocument();
  });

  it("既存テーブルをクリックすると DataPreview に遷移する", async () => {
    const user = userEvent.setup();
    render(<LeftSideMenu />);

    await user.click(screen.getByText("sales"));

    await waitFor(() => {
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      expect(useTableInfosStore.getState().activeTableName).toBe("sales");
    });
  });

  it("左メニューに work tab 起動導線は表示しない", () => {
    render(<LeftSideMenu />);

    expect(screen.queryByTestId("left-menu-work-actions")).toBeNull();
  });

  it("結果タブへ切り替えると fetchSummaries が呼ばれる", async () => {
    const user = userEvent.setup();
    const fetchSummaries = vi.fn().mockResolvedValue(undefined);
    useAnalysisResultsStore.setState({ fetchSummaries });
    render(<LeftSideMenu />);

    await user.click(screen.getByTestId("left-menu-tab-results"));

    await waitFor(() => {
      expect(fetchSummaries).toHaveBeenCalled();
    });
  });

  it("結果項目クリックで結果タブが開き DataPreview に遷移する", async () => {
    const user = userEvent.setup();
    const openResult = vi.fn().mockResolvedValue(MOCK_RESULT_DETAIL);
    useAnalysisResultsStore.setState({
      pane: "results",
      summaries: [
        {
          id: "result-1",
          name: "OLS 1",
          description: "desc",
          createdAt: "2026-04-29T10:15:30Z",
          tableName: "sales",
          resultType: "regression",
          resultTypeLabel: "回帰分析",
          modelType: "ols",
          summaryText: "OLS / price",
        },
      ],
      openResult,
    });
    render(<LeftSideMenu />);

    await user.click(screen.getByTestId("analysis-result-open-result-1"));

    await waitFor(() => {
      expect(openResult).toHaveBeenCalledWith("result-1");
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe(
        "result:result-1",
      );
    });
  });

  it("既に開いている結果は再取得せず再アクティブ化する", async () => {
    const user = userEvent.setup();
    const openResult = vi.fn();
    useWorkspaceTabsStore.setState({
      tabs: [
        {
          id: "result:result-1",
          kind: "result",
          title: "OLS 1",
          resultId: "result-1",
          resultType: "regression",
          detail: MOCK_RESULT_DETAIL,
        },
      ],
      activeTabId: null,
    });
    useAnalysisResultsStore.setState({
      pane: "results",
      summaries: [
        {
          id: "result-1",
          name: "OLS 1",
          description: "desc",
          createdAt: "2026-04-29T10:15:30Z",
          tableName: "sales",
          resultType: "regression",
          resultTypeLabel: "回帰分析",
          modelType: "ols",
          summaryText: "OLS / price",
        },
      ],
      openResult,
    });
    render(<LeftSideMenu />);

    await user.click(screen.getByTestId("analysis-result-open-result-1"));

    await waitFor(() => {
      expect(openResult).not.toHaveBeenCalled();
      expect(useWorkspaceTabsStore.getState().activeTabId).toBe(
        "result:result-1",
      );
    });
  });

  it("結果削除で確認後に deleteAnalysisResult が呼ばれる", async () => {
    const user = userEvent.setup();
    mockApi.deleteAnalysisResult.mockResolvedValue({ code: "OK" });
    const removeSummary = vi.fn();
    useAnalysisResultsStore.setState({
      pane: "results",
      summaries: [
        {
          id: "result-1",
          name: "OLS 1",
          description: "desc",
          createdAt: "2026-04-29T10:15:30Z",
          tableName: "sales",
          resultType: "regression",
          resultTypeLabel: "回帰分析",
          modelType: "ols",
          summaryText: "OLS / price",
        },
      ],
      removeSummary,
    });
    render(<LeftSideMenu />);

    await user.click(screen.getByTestId("analysis-result-delete-result-1"));

    await waitFor(() => {
      expect(vi.mocked(showConfirmDialog)).toHaveBeenCalled();
      expect(mockApi.deleteAnalysisResult).toHaveBeenCalledWith("result-1");
      expect(removeSummary).toHaveBeenCalledWith("result-1");
    });
  });

  it("結果取得に失敗した場合はエラーダイアログを表示する", async () => {
    const user = userEvent.setup();
    const openResult = vi.fn().mockRejectedValue(new Error("取得失敗"));
    useAnalysisResultsStore.setState({
      pane: "results",
      summaries: [
        {
          id: "result-1",
          name: "OLS 1",
          description: "desc",
          createdAt: "2026-04-29T10:15:30Z",
          tableName: "sales",
          resultType: "regression",
          resultTypeLabel: "回帰分析",
          modelType: "ols",
          summaryText: "OLS / price",
        },
      ],
      openResult,
    });
    render(<LeftSideMenu />);

    await user.click(screen.getByTestId("analysis-result-open-result-1"));

    await waitFor(() => {
      expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
        "Error.Error",
        "取得失敗",
      );
    });
  });
});
