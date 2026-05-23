import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { GroupStatistics } from "@/components/pages/GroupStatistics";
import { showMessageDialog } from "@/lib/dialog/message";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
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

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));
vi.mock("../../lib/utils/internal", () => ({
  getTableInfo: vi.fn().mockResolvedValue({
    tableName: "grouped_sales",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));

const mockTableLoader = vi.hoisted(() => ({
  selectedTableName: "sales",
  setSelectedTableName: vi.fn(),
  columnList: [
    { name: "region", type: "String" },
    { name: "sales", type: "Float64" },
  ],
  setColumnList: vi.fn(),
  isLoading: false,
}));

vi.mock("../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({ ...mockTableLoader }),
}));

const mockApi = {
  createGroupStatisticsTable: vi.fn(),
};

const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

const goToStep2 = async (user: ReturnType<typeof userEvent.setup>) => {
  await act(async () => {
    await user.click(screen.getByText("GroupStatistics.NextStep"));
  });
};

beforeEach(() => {
  vi.clearAllMocks();
  mockTableLoader.selectedTableName = "sales";
  mockTableLoader.columnList = [
    { name: "region", type: "String" },
    { name: "sales", type: "Float64" },
  ];
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
  useTableInfosStore.setState({ tableInfos: [], activeTableName: "sales" });
  useCurrentPageStore.setState({ currentView: "Workspace" });
  useWorkspaceTabsStore.setState({
    tabs: [
      {
        id: "work:GroupStatistics",
        kind: "work",
        title: "グループ別統計量",
        featureKey: "GroupStatistics",
        dirty: true,
        createdAt: Date.now(),
        draftValues: {
          tableName: "sales",
          groupByColumns: ["region"],
          statColumns: ["sales"],
          statistics: [DescriptiveStatisticType.mean],
          newTableName: "grouped_sales",
        },
        committedValues: {
          tableName: "sales",
          groupByColumns: [],
          statColumns: [],
          statistics: [],
          newTableName: "",
        },
      },
    ],
    activeTabId: "work:GroupStatistics",
  });
});

describe("GroupStatistics", () => {
  it("2 ステップ Wizard で Step 1 と Step 2 を往復できる", async () => {
    const user = userEvent.setup();
    render(<GroupStatistics workTabId="work:GroupStatistics" />);

    expect(screen.getByText("GroupStatistics.Step1Lead")).toBeInTheDocument();

    await goToStep2(user);

    expect(screen.getByText("GroupStatistics.Step2Lead")).toBeInTheDocument();
    expect(
      screen.getByTestId("group-statistics-role-matrix"),
    ).toBeInTheDocument();

    await user.click(screen.getByText("Common.Back"));

    expect(screen.getByText("GroupStatistics.Step1Lead")).toBeInTheDocument();
  });

  it("成功時は新しいテーブル名を tableList に追加して Workspace に戻る", async () => {
    const user = userEvent.setup();
    mockApi.createGroupStatisticsTable.mockResolvedValue({
      code: "OK",
      result: { tableName: "grouped_sales" },
    });

    render(<GroupStatistics workTabId="work:GroupStatistics" />);

    await goToStep2(user);
    await submitForm();

    await waitFor(() => {
      expect(mockApi.createGroupStatisticsTable).toHaveBeenCalledTimes(1);
    });

    expect(useTableListStore.getState().tableList).toContain("grouped_sales");
    expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
  });

  it("newTableName を含む API エラーはフォーム入力名に置換して表示する", async () => {
    const user = userEvent.setup();
    mockApi.createGroupStatisticsTable.mockResolvedValue({
      code: "TABLE_ALREADY_EXISTS",
      message: "newTableName 'grouped_sales'は既に存在します。",
    });

    render(<GroupStatistics workTabId="work:GroupStatistics" />);

    await goToStep2(user);
    await submitForm();

    await waitFor(() => {
      expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
        "Error.Error",
        "GroupStatistics.OutputDataLabel 'grouped_sales'は既に存在します。",
      );
    });
  });
});
