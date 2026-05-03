import { WorkspaceSurface } from "@/components/pages/WorkspaceSurface";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("@/lib/dialog/confirm", () => ({
  showConfirmDialog: vi.fn().mockResolvedValue(true),
}));

vi.mock("../organisms/Table/VirtualTable", () => ({
  VirtualTable: ({ tableInfo }: { tableInfo: { tableName: string } }) => (
    <div data-testid={`virtual-table-${tableInfo.tableName}`} />
  ),
}));

vi.mock("./JoinTable", () => ({
  JoinTable: () => <input data-testid="work-join-input" defaultValue="" />,
}));
vi.mock("./UnionTable", () => ({
  UnionTable: () => <div data-testid="work-union" />,
}));
vi.mock("./CreateSimulationDataTable", () => ({
  CreateSimulationDataTable: () => <div data-testid="work-sim" />,
}));
vi.mock("./Calculation", () => ({
  Calculation: () => <div data-testid="work-calc" />,
}));
vi.mock("./ConfidenceIntervalView", () => ({
  ConfidenceIntervalView: () => <div data-testid="work-ci" />,
}));
vi.mock("./RegressionView", () => ({
  Regression: () => <div data-testid="work-reg" />,
}));
vi.mock("./CorrelationMatrix", () => ({
  CorrelationMatrix: () => <div data-testid="work-corr" />,
}));

const TABLE_SALES = {
  tableName: "sales",
  columnList: [{ name: "price", type: "Float64" }],
  totalRows: 10,
  isActive: true,
};

beforeEach(() => {
  vi.clearAllMocks();
  useCurrentPageStore.setState({ currentView: "DataPreview" });
  useTableInfosStore.setState({
    tableInfos: [TABLE_SALES],
    activeTableName: "sales",
  });
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
    openResult: vi.fn(),
    removeSummary: vi.fn(),
    upsertSummary: vi.fn(),
    clearActiveResult: vi.fn(),
  });
});

describe("WorkspaceSurface コンポーネント", () => {
  it("アクティブなテーブルの VirtualTable が表示される", () => {
    render(<WorkspaceSurface />);
    expect(screen.getByTestId("virtual-table-sales")).toBeInTheDocument();
  });

  it("work tab がアクティブなとき対応画面を表示する", () => {
    useWorkspaceTabsStore.setState({
      tabs: [
        {
          id: "work:JoinTable",
          kind: "work",
          title: "Join",
          featureKey: "JoinTable",
          dirty: false,
        },
      ],
      activeTabId: "work:JoinTable",
    });
    useCurrentPageStore.setState({ currentView: "JoinTable" });

    render(<WorkspaceSurface />);

    expect(screen.getByTestId("workspace-work-tab-JoinTable")).toBeInTheDocument();
    expect(screen.getByTestId("work-join-input")).toBeInTheDocument();
  });

  it("CorrelationMatrix の work tab も WorkspaceSurface 経由で表示する", () => {
    useWorkspaceTabsStore.setState({
      tabs: [
        {
          id: "work:CorrelationMatrix",
          kind: "work",
          title: "相関行列",
          featureKey: "CorrelationMatrix",
          dirty: false,
          createdAt: Date.now(),
        },
      ],
      activeTabId: "work:CorrelationMatrix",
    });
    useCurrentPageStore.setState({ currentView: "CorrelationMatrix" });

    render(<WorkspaceSurface />);

    expect(
      screen.getByTestId("workspace-work-tab-CorrelationMatrix"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("work-corr")).toBeInTheDocument();
  });

  it("work tab で入力すると dirty になり、閉じる時に確認する", async () => {
    const user = userEvent.setup();
    vi.mocked(showConfirmDialog).mockResolvedValue(false);
    useWorkspaceTabsStore.setState({
      tabs: [
        {
          id: "work:JoinTable",
          kind: "work",
          title: "Join",
          featureKey: "JoinTable",
          dirty: false,
        },
      ],
      activeTabId: "work:JoinTable",
    });
    useCurrentPageStore.setState({ currentView: "JoinTable" });

    render(<WorkspaceSurface />);

    await user.type(screen.getByTestId("work-join-input"), "a");
    const workTab = screen.getByText("Join").closest("[role='button']")!;
    const closeButton = workTab.querySelector("button") as HTMLButtonElement;
    await user.click(closeButton);

    await waitFor(() => {
      expect(vi.mocked(showConfirmDialog)).toHaveBeenCalled();
      const workTab = useWorkspaceTabsStore
        .getState()
        .tabs.find((tab) => tab.kind === "work");
      expect(workTab).toMatchObject({
        kind: "work",
        dirty: true,
      });
    });
  });
});