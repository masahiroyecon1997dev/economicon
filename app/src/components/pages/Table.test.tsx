import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTableInfosStore } from "@/stores/tableInfos";
import { Table } from "@/components/pages/Table";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// VirtualTable は重量コンポーネントなのでスタブ化
vi.mock("../organisms/Table/VirtualTable", () => ({
  VirtualTable: ({ tableInfo }: { tableInfo: { tableName: string } }) => (
    <div data-testid={`virtual-table-${tableInfo.tableName}`} />
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const TABLE_SALES = {
  tableName: "sales",
  columnList: [{ name: "price", type: "Float64" }],
  totalRows: 10,
  isActive: true,
};
const TABLE_COSTS = {
  tableName: "costs",
  columnList: [{ name: "amount", type: "Float64" }],
  totalRows: 5,
  isActive: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  useTableInfosStore.setState({
    tableInfos: [TABLE_SALES, TABLE_COSTS],
    activeTableName: "sales",
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("Table コンポーネント", () => {
  describe("タブ表示", () => {
    it("テーブル数分のタブが表示される", () => {
      render(<Table />);
      expect(screen.getByText("sales")).toBeInTheDocument();
      expect(screen.getByText("costs")).toBeInTheDocument();
    });

    it("アクティブなテーブルのタブが強調表示（border-brand-primary）される", () => {
      render(<Table />);
      const salesTab = screen.getByText("sales").closest("[role='button']");
      expect(salesTab).toHaveClass("border-brand-primary");
    });

    it("非アクティブなテーブルのタブはデフォルトスタイル", () => {
      render(<Table />);
      const costsTab = screen.getByText("costs").closest("[role='button']");
      expect(costsTab).toHaveClass("border-transparent");
    });

    it("テーブルが0件の場合はタブが表示されない", () => {
      useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
      render(<Table />);
      expect(screen.queryByRole("button")).toBeNull();
    });
  });

  describe("タブ操作", () => {
    it("非アクティブなタブをクリックするとアクティブになる", async () => {
      const user = userEvent.setup();
      render(<Table />);

      const costsTab = screen.getByText("costs").closest("[role='button']")!;
      await user.click(costsTab);

      await waitFor(() => {
        const state = useTableInfosStore.getState();
        expect(state.activeTableName).toBe("costs");
      });
    });

    it("×ボタンをクリックするとテーブルがタブから削除される", async () => {
      const user = userEvent.setup();
      render(<Table />);

      const closeButtons = screen.getAllByRole("button", {
        name: "Table.CloseTab",
      });
      // costs タブの×ボタン
      await user.click(closeButtons[1]);

      await waitFor(() => {
        expect(screen.queryByText("costs")).toBeNull();
      });
    });

    it("×ボタンクリックでタブクリックイベントが発火しない", async () => {
      const user = userEvent.setup();
      render(<Table />);

      // sales がアクティブの状態で costs の×ボタンをクリック
      const closeButtons = screen.getAllByRole("button", {
        name: "Table.CloseTab",
      });
      await user.click(closeButtons[1]);

      // sales は依然アクティブのまま
      await waitFor(() => {
        expect(useTableInfosStore.getState().activeTableName).toBe("sales");
      });
    });
  });

  describe("テーブル本体", () => {
    it("アクティブなテーブルの VirtualTable が表示される", () => {
      render(<Table />);
      expect(screen.getByTestId("virtual-table-sales")).toBeInTheDocument();
    });

    it("非アクティブなテーブルの VirtualTable は表示されない", () => {
      render(<Table />);
      expect(screen.queryByTestId("virtual-table-costs")).toBeNull();
    });
  });

  describe("キーボード操作", () => {
    it("Enterキーでタブがアクティブになる", async () => {
      const user = userEvent.setup();
      render(<Table />);

      const costsTab = screen
        .getByText("costs")
        .closest("[role='button']") as HTMLElement;
      costsTab.focus();
      await user.keyboard("{Enter}");

      await waitFor(() => {
        expect(useTableInfosStore.getState().activeTableName).toBe("costs");
      });
    });
  });
});
