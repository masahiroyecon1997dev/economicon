import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { DescriptiveStatistics } from "@/components/pages/DescriptiveStatistics";
import { showMessageDialog } from "@/lib/dialog/message";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
const fixedT = (key: string, opts?: Record<string, string>) => {
  if (!opts) return key;
  return Object.entries(opts).reduce(
    (s, [k, v]) => s.replace(`{{${k}}}`, v),
    key,
  );
};

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: fixedT,
  }),
}));

vi.mock("../../api/endpoints");
vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));
const mockSetCurrentView = vi.fn();
vi.mock("../../stores/currentView", () => ({
  useCurrentPageStore: vi.fn(
    (
      selector: (state: {
        setCurrentView: typeof mockSetCurrentView;
      }) => unknown,
    ) => selector({ setCurrentView: mockSetCurrentView }),
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const COLUMNS = [
  { name: "price", type: "Float64" },
  { name: "quantity", type: "Int64" },
];

const mockApi = {
  getColumnList: vi.fn(),
  descriptiveStatistics: vi.fn(),
  getAnalysisResult: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  mockSetCurrentView.mockReset();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales"] });
  useWorkspaceTabsStore.setState({ tabs: [], activeTabId: null });
  useAnalysisResultsStore.setState((state) => ({
    ...state,
    fetchSummaries: vi.fn().mockResolvedValue(undefined),
  }));
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("DescriptiveStatistics フォーム", () => {
  describe("empty state", () => {
    it("テーブルが 0 件なら NoTables state を表示し、ImportDataFile に遷移できる", async () => {
      const user = userEvent.setup();
      useTableListStore.setState({ tableList: [] });

      render(<DescriptiveStatistics />);

      expect(
        screen.getByTestId("analysis-no-tables-state"),
      ).toBeInTheDocument();

      await user.click(
        screen.getByRole("button", {
          name: "AnalysisEmptyState.NoTablesAction",
        }),
      );

      expect(mockSetCurrentView).toHaveBeenCalledWith("ImportDataFile");
    });

    it("列ロード中は共通 loading state を表示する", async () => {
      mockApi.getColumnList.mockReturnValue(new Promise(() => {}));
      const user = userEvent.setup();

      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      expect(
        await screen.findByTestId(
          "descriptive-statistics-loading-columns-state",
        ),
      ).toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("テーブル未選択でサブミットするとテーブル選択エラーが表示される", async () => {
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("DescriptiveStatistics.ErrorDataRequired"),
        ).toBeInTheDocument();
      });
    });

    it("列チェックが0件でサブミットするとエラーが表示される", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: COLUMNS },
      });
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      // テーブルを選択（Select コンポーネント）
      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      // 列チェックをすべて外す
      await waitFor(() => {
        expect(screen.getByText("price")).toBeInTheDocument();
      });
      const deselectAllBtn = screen.getAllByRole("button", {
        name: /DeselectAll|すべて解除/i,
      })[0];
      await user.click(deselectAllBtn);

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText("DescriptiveStatistics.ErrorColumnsRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("初期状態のまま送信すると既定の統計量セットだけを送る", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: COLUMNS },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: {
          id: "test-result-id",
          name: "sales descriptive statistics",
          resultType: "descriptive_statistics",
          resultData: {
            statistics: {
              price: { [DescriptiveStatisticType.mean]: 24.5 },
            },
          },
        },
      });

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      await user.click(
        screen.getByRole("button", {
          name: "DescriptiveStatistics.RunCalculation",
        }),
      );

      await waitFor(() => {
        expect(mockApi.descriptiveStatistics).toHaveBeenCalledWith({
          tableName: "sales",
          columnNameList: ["price", "quantity"],
          statistics: [
            DescriptiveStatisticType.count,
            DescriptiveStatisticType.mean,
            DescriptiveStatisticType.median,
            DescriptiveStatisticType.std_dev,
            DescriptiveStatisticType.min,
            DescriptiveStatisticType.max,
          ],
        });
      });
    });

    it("計算成功時は result tab を開いて DataPreview に戻る", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: {
          id: "test-result-id",
          name: "sales descriptive statistics",
          resultType: "descriptive_statistics",
          resultData: {
            statistics: {
              price: { [DescriptiveStatisticType.mean]: 24.5 },
            },
          },
        },
      });
      const fetchSummaries = vi.fn().mockResolvedValue(undefined);
      useAnalysisResultsStore.setState((state) => ({
        ...state,
        fetchSummaries,
      }));

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(useWorkspaceTabsStore.getState().activeTabId).toBe(
          "result:test-result-id",
        );
        expect(fetchSummaries).toHaveBeenCalled();
        expect(mockSetCurrentView).toHaveBeenCalledWith("DataPreview");
      });
      expect(
        screen.queryByText("DescriptiveStatistics.ResultTitle"),
      ).not.toBeInTheDocument();
    });

    it("work tab モードでは保存済み draft を使ってそのまま送信できる", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockResolvedValue({
        code: "OK",
        result: {
          id: "test-result-id",
          name: "sales descriptive statistics",
          resultType: "descriptive_statistics",
          resultData: {
            statistics: {
              price: { [DescriptiveStatisticType.mean]: 24.5 },
            },
          },
        },
      });
      useWorkspaceTabsStore.setState({
        tabs: [
          {
            id: "work:DescriptiveStatistics",
            kind: "work",
            title: "基本統計量",
            featureKey: "DescriptiveStatistics",
            dirty: true,
            createdAt: Date.now(),
            draftValues: {
              tableName: "sales",
              columnNames: ["price"],
              statistics: [DescriptiveStatisticType.mean],
            },
            committedValues: {
              tableName: "sales",
              columnNames: [],
              statistics: [],
            },
          },
        ],
        activeTabId: "work:DescriptiveStatistics",
      });

      const user = userEvent.setup();
      render(<DescriptiveStatistics workTabId="work:DescriptiveStatistics" />);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(mockApi.descriptiveStatistics).toHaveBeenCalledWith({
          tableName: "sales",
          columnNameList: ["price"],
          statistics: [DescriptiveStatisticType.mean],
        });
      });
    });
  });

  describe("API失敗時", () => {
    it("getColumnList がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockRejectedValue(new Error("ネットワークエラー"));
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });

    it("descriptiveStatistics がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockRejectedValue(
        new Error("サーバーエラー"),
      );

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });

    it("getAnalysisResult がthrowした場合 → エラーダイアログを表示する", async () => {
      mockApi.getColumnList.mockResolvedValue({
        code: "OK",
        result: { columnInfoList: [{ name: "price", type: "Float64" }] },
      });
      mockApi.descriptiveStatistics.mockResolvedValue({
        code: "OK",
        result: { resultId: "test-result-id" },
      });
      mockApi.getAnalysisResult.mockRejectedValue(new Error("詳細取得エラー"));

      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const selectTrigger = screen.getByRole("combobox");
      await user.click(selectTrigger);
      const option = await screen.findByRole("option", { name: "sales" });
      await user.click(option);

      await waitFor(() =>
        expect(screen.getByText("price")).toBeInTheDocument(),
      );

      const submitBtn = screen.getByRole("button", {
        name: "DescriptiveStatistics.RunCalculation",
      });
      await user.click(submitBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalled();
      });
    });
  });

  describe("キャンセル", () => {
    it("通常モードでは DataPreview に戻る", async () => {
      const user = userEvent.setup();
      render(<DescriptiveStatistics />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(mockSetCurrentView).toHaveBeenCalledWith("DataPreview");
    });

    it("work tab モードでは onCancel を呼ぶ", async () => {
      const user = userEvent.setup();
      const onCancel = vi.fn();
      render(
        <DescriptiveStatistics
          workTabId="work:DescriptiveStatistics"
          onCancel={onCancel}
        />,
      );

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
