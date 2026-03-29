import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { LeftSideMenu } from "./LeftSideMenu";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("../../lib/dialog/message", () => ({
  showMessageDialog: vi.fn().mockResolvedValue(undefined),
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

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
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
  useCurrentPageStore.setState({ currentView: "ImportDataFile" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("LeftSideMenu コンポーネント", () => {
  describe("初期レンダリング", () => {
    it("データリストのセクション見出しが表示される", () => {
      render(<LeftSideMenu />);
      expect(screen.getByText("LeftSideMenu.DataList")).toBeInTheDocument();
    });

    it("TableNav コンポーネントが表示される", () => {
      render(<LeftSideMenu />);
      expect(screen.getByText("sales")).toBeInTheDocument();
    });
  });

  describe("テーブルクリック — 既存テーブル", () => {
    it("既にキャッシュ済みのテーブルをクリックすると activateTableInfo が呼ばれ DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<LeftSideMenu />);

      await user.click(screen.getByText("sales"));

      await waitFor(() => {
        expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
        expect(useTableInfosStore.getState().activeTableName).toBe("sales");
      });
    });
  });

  describe("テーブルクリック — 新規テーブル（キャッシュなし）", () => {
    it("未キャッシュのテーブルをクリックすると getTableInfo を呼び DataPreview に遷移する", async () => {
      const { getTableInfo } = await import("../../lib/utils/internal");
      const user = userEvent.setup();
      render(<LeftSideMenu />);

      await user.click(screen.getByText("new_table"));

      await waitFor(() => {
        expect(vi.mocked(getTableInfo)).toHaveBeenCalledWith("new_table");
        expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
      });
    });
  });

  describe("エラー処理", () => {
    it("getTableInfo がthrowした場合 → エラーダイアログを表示する", async () => {
      const { getTableInfo } = await import("../../lib/utils/internal");
      vi.mocked(getTableInfo).mockRejectedValueOnce(
        new Error("テーブル取得失敗"),
      );
      const user = userEvent.setup();
      render(<LeftSideMenu />);

      await user.click(screen.getByText("new_table"));

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "テーブル取得失敗",
        );
      });
      // 遷移はしない
      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });
  });
});
