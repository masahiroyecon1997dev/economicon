import { ChartView } from "@/components/pages/ChartView";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

vi.mock("plotly.js-dist-min", () => ({
  react: vi.fn().mockResolvedValue(undefined),
  purge: vi.fn(),
  newPlot: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("apache-arrow", () => ({
  tableFromIPC: vi.fn(() => ({
    getChild: vi.fn(() => null),
  })),
}));

vi.mock("@/api/bridge/tauri-commands", () => ({
  fetchPlotDataBinary: vi.fn().mockResolvedValue(new Uint8Array([])),
}));

vi.mock("@/lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
}));

const mockTableLoader = vi.hoisted(() => ({
  selectedTableName: "",
  setSelectedTableName: vi.fn(),
  columnList: [] as { name: string; type: string }[],
  setColumnList: vi.fn(),
  isLoading: false,
}));

vi.mock("@/hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({ ...mockTableLoader }),
}));

// Select を native select に置き換え（Radix UI は jsdom 非対応）
vi.mock("@/components/atoms/Input/Select", () => ({
  Select: ({
    value,
    onValueChange,
    children,
    placeholder,
    ...props
  }: {
    value: string;
    onValueChange: (v: string) => void;
    children: React.ReactNode;
    placeholder?: string;
    [key: string]: unknown;
  }) => (
    <select
      value={value}
      onChange={(e) => onValueChange(e.target.value)}
      aria-label={placeholder}
      {...(props as React.SelectHTMLAttributes<HTMLSelectElement>)}
    >
      <option value="">{placeholder}</option>
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

// ---------------------------------------------------------------------------
// State helpers
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
  mockTableLoader.selectedTableName = "";
  mockTableLoader.columnList = [];
  mockTableLoader.isLoading = false;
  useTableListStore.setState({ tableList: [] });
  useTableInfosStore.setState({ activeTableName: null });
  useCurrentPageStore.setState({ currentView: "Workspace" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("ChartView", () => {
  describe("テーブルなしの場合", () => {
    it("test_render_noTables_showsNoTablesState", () => {
      render(<ChartView />);
      expect(
        screen.getByTestId("analysis-no-tables-state"),
      ).toBeInTheDocument();
    });

    it("test_render_noTables_doesNotShowChartPanel", () => {
      render(<ChartView />);
      expect(screen.queryByTestId("chart-view-panel")).not.toBeInTheDocument();
    });
  });

  describe("テーブルあり", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales", "inventory"] });
    });

    it("test_render_withTables_showsTableSelector", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-view-table-select")).toBeInTheDocument();
    });

    it("test_render_withTables_showsChartPanel", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-view-panel")).toBeInTheDocument();
    });

    it("test_render_withTables_showsChartTypButtons", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-type-scatter")).toBeInTheDocument();
      expect(screen.getByTestId("chart-type-histogram")).toBeInTheDocument();
      expect(screen.getByTestId("chart-type-line")).toBeInTheDocument();
    });

    it("test_render_initialEmpty_showsEmptyState", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-view-empty")).toBeInTheDocument();
    });
  });

  describe("チャートタイプ選択", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales"] });
    });

    it("test_chartType_scatter_isDefaultSelected", () => {
      render(<ChartView />);
      const btn = screen.getByTestId("chart-type-scatter");
      expect(btn.className).toMatch(/border-brand-primary/);
    });

    it("test_chartType_clickHistogram_changesSelection", () => {
      render(<ChartView />);
      const histBtn = screen.getByTestId("chart-type-histogram");
      fireEvent.click(histBtn);
      expect(histBtn.className).toMatch(/border-brand-primary/);
    });

    it("test_chartType_clickLine_changesSelection", () => {
      render(<ChartView />);
      const lineBtn = screen.getByTestId("chart-type-line");
      fireEvent.click(lineBtn);
      expect(lineBtn.className).toMatch(/border-brand-primary/);
    });
  });

  describe("カラム選択パネル", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales"] });
      mockTableLoader.selectedTableName = "sales";
      mockTableLoader.columnList = [
        { name: "price", type: "Float64" },
        { name: "quantity", type: "Float64" },
      ];
    });

    it("test_columnPanel_showsXColumnSelector", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-view-x-column")).toBeInTheDocument();
    });

    it("test_columnPanel_scatter_showsYColumnSelector", () => {
      render(<ChartView />);
      expect(screen.getByTestId("chart-view-y-column")).toBeInTheDocument();
    });

    it("test_columnPanel_histogram_hidesYColumnSelector", () => {
      render(<ChartView />);
      fireEvent.click(screen.getByTestId("chart-type-histogram"));
      expect(
        screen.queryByTestId("chart-view-y-column"),
      ).not.toBeInTheDocument();
    });
  });

  describe("ローディング中", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales"] });
      mockTableLoader.selectedTableName = "sales";
      mockTableLoader.isLoading = true;
    });

    it("test_loading_showsLoadingColumns", () => {
      render(<ChartView />);
      expect(
        screen.getByTestId("chart-view-loading-columns"),
      ).toBeInTheDocument();
    });
  });

  describe("onCancel", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: [] });
    });

    it("test_cancel_withoutProp_navigatesToWorkspace", () => {
      render(<ChartView />);
      const cancelBtn = screen.getByRole("button", { name: /Common\.Cancel/i });
      fireEvent.click(cancelBtn);
      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
    });

    it("test_cancel_withProp_callsCallback", () => {
      const onCancel = vi.fn().mockResolvedValue(undefined);
      render(<ChartView onCancel={onCancel} />);
      fireEvent.click(screen.getByRole("button", { name: /Common\.Cancel/i }));
      expect(onCancel).toHaveBeenCalledOnce();
    });
  });
});
