import { PlotView } from "@/components/pages/PlotView";
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
describe("PlotView", () => {
  describe("テーブルなしの場合", () => {
    it("test_render_noTables_showsNoTablesState", () => {
      render(<PlotView />);
      expect(
        screen.getByTestId("analysis-no-tables-state"),
      ).toBeInTheDocument();
    });

    it("test_render_noTables_doesNotShowPlotPanel", () => {
      render(<PlotView />);
      expect(screen.queryByTestId("plot-view-panel")).not.toBeInTheDocument();
    });
  });

  describe("テーブルあり", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales", "inventory"] });
    });

    it("test_render_withTables_showsTableSelector", () => {
      render(<PlotView />);
      expect(screen.getByTestId("plot-view-table-select")).toBeInTheDocument();
    });

    it("test_render_withTables_showsPlotPanel", () => {
      render(<PlotView />);
      expect(screen.getByTestId("plot-view-panel")).toBeInTheDocument();
    });

    it("test_render_withTables_showsPlotTypButtons", () => {
      render(<PlotView />);
      expect(screen.getByTestId("plot-type-scatter")).toBeInTheDocument();
      expect(screen.getByTestId("plot-type-histogram")).toBeInTheDocument();
      expect(screen.getByTestId("plot-type-line")).toBeInTheDocument();
    });

    it("test_render_initialEmpty_showsEmptyState", () => {
      render(<PlotView />);
      expect(screen.getByTestId("plot-view-empty")).toBeInTheDocument();
    });
  });

  describe("チャートタイプ選択", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: ["sales"] });
    });

    it("test_plotType_scatter_isDefaultSelected", () => {
      render(<PlotView />);
      const btn = screen.getByTestId("plot-type-scatter");
      expect(btn.className).toMatch(/border-brand-primary/);
    });

    it("test_plotType_clickHistogram_changesSelection", () => {
      render(<PlotView />);
      const histBtn = screen.getByTestId("plot-type-histogram");
      fireEvent.click(histBtn);
      expect(histBtn.className).toMatch(/border-brand-primary/);
    });

    it("test_plotType_clickLine_changesSelection", () => {
      render(<PlotView />);
      const lineBtn = screen.getByTestId("plot-type-line");
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
      render(<PlotView />);
      expect(screen.getByTestId("plot-view-x-column")).toBeInTheDocument();
    });

    it("test_columnPanel_scatter_showsYColumnSelector", () => {
      render(<PlotView />);
      expect(screen.getByTestId("plot-view-y-column")).toBeInTheDocument();
    });

    it("test_columnPanel_histogram_hidesYColumnSelector", () => {
      render(<PlotView />);
      fireEvent.click(screen.getByTestId("plot-type-histogram"));
      expect(
        screen.queryByTestId("plot-view-y-column"),
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
      render(<PlotView />);
      expect(
        screen.getByTestId("plot-view-loading-columns"),
      ).toBeInTheDocument();
    });
  });

  describe("onCancel", () => {
    beforeEach(() => {
      useTableListStore.setState({ tableList: [] });
    });

    it("test_cancel_withoutProp_navigatesToWorkspace", () => {
      render(<PlotView />);
      const cancelBtn = screen.getByRole("button", { name: /Common\.Cancel/i });
      fireEvent.click(cancelBtn);
      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
    });

    it("test_cancel_withProp_callsCallback", () => {
      const onCancel = vi.fn().mockResolvedValue(undefined);
      render(<PlotView onCancel={onCancel} />);
      fireEvent.click(screen.getByRole("button", { name: /Common\.Cancel/i }));
      expect(onCancel).toHaveBeenCalledOnce();
    });
  });
});
