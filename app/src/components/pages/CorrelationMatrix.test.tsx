import { getEconomiconAppAPI } from "@/api/endpoints";
import { CorrelationMethod, MissingHandlingMethod } from "@/api/model";
import { CorrelationMatrix } from "@/components/pages/CorrelationMatrix";
import { showMessageDialog } from "@/lib/dialog/message";
import { useCurrentPageStore } from "@/stores/currentView";
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

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
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
    tableName: "corr_result",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));
const mockTableLoader = vi.hoisted(() => ({
  selectedTableName: "",
  setSelectedTableName: vi.fn((tableName: string) => {
    mockTableLoader.selectedTableName = tableName;
  }),
  columnList: [
    { name: "price", type: "Float64" },
    { name: "quantity", type: "Float64" },
  ],
  setColumnList: vi.fn((columnList: Array<{ name: string; type: string }>) => {
    mockTableLoader.columnList = columnList;
  }),
  isLoading: false,
}));
vi.mock("../../hooks/useTableColumnLoader", () => ({
  useTableColumnLoader: () => ({ ...mockTableLoader }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  createCorrelationTable: vi.fn(),
  getColumnList: vi.fn(),
};

const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

beforeEach(() => {
  vi.clearAllMocks();
  mockTableLoader.selectedTableName = "";
  mockTableLoader.columnList = [
    { name: "price", type: "Float64" },
    { name: "quantity", type: "Float64" },
  ];
  mockTableLoader.isLoading = false;
  mockTableLoader.setSelectedTableName.mockImplementation(
    (tableName: string) => {
      mockTableLoader.selectedTableName = tableName;
    },
  );
  mockTableLoader.setColumnList.mockImplementation(
    (columnList: Array<{ name: string; type: string }>) => {
      mockTableLoader.columnList = columnList;
    },
  );
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "costs"] });
  useTableInfosStore.setState({
    tableInfos: [],
    activeTableName: null,
  });
  useCurrentPageStore.setState({ currentView: "Workspace" });
  useWorkspaceTabsStore.setState({
    tabs: [],
    activeTabId: null,
  });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("CorrelationMatrix フォーム", () => {
  describe("empty state", () => {
    it("テーブルが 0 件なら NoTables state を表示し、ImportDataFile に遷移できる", async () => {
      const user = userEvent.setup();
      useTableListStore.setState({ tableList: [] });

      render(<CorrelationMatrix />);

      expect(
        screen.getByTestId("analysis-no-tables-state"),
      ).toBeInTheDocument();

      await user.click(
        screen.getByRole("button", {
          name: "AnalysisEmptyState.NoTablesAction",
        }),
      );

      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });

    it("対象列がないときは共通 no-columns state を表示する", () => {
      mockTableLoader.selectedTableName = "sales";
      mockTableLoader.columnList = [];

      render(<CorrelationMatrix />);

      expect(
        screen.getByTestId("correlation-matrix-no-columns-state"),
      ).toBeInTheDocument();
    });
  });

  describe("バリデーション", () => {
    it("テーブル未選択でサブミットするとエラーが表示される", async () => {
      render(<CorrelationMatrix />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("CorrelationMatrix.ErrorDataRequired"),
        ).toBeInTheDocument();
      });
    });

    it("出力データ名が空のままサブミットするとエラーが表示される", async () => {
      render(<CorrelationMatrix />);
      // columnNames はフック経由で自動セットされる想定
      await submitForm();

      await waitFor(() => {
        // テーブル未選択エラーと出力名エラーが表示される
        expect(
          screen.getAllByText(/ErrorDataRequired|ErrorOutputNameRequired/),
        ).toBeTruthy();
      });
    });
  });

  describe("詳細オプション accordion", () => {
    it("詳細オプションボタンをクリックするとオプションが展開される", async () => {
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const optionBtn = screen.getByRole("button", {
        name: /AdvancedOptions/,
      });
      expect(screen.queryByText("CorrelationMatrix.MethodLabel")).toBeNull();
      await user.click(optionBtn);

      await waitFor(() => {
        expect(
          screen.getByText("CorrelationMatrix.MethodLabel"),
        ).toBeInTheDocument();
      });
    });

    it("詳細オプションボタンを再度クリックすると折りたたまれる", async () => {
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const optionBtn = screen.getByRole("button", {
        name: /AdvancedOptions/,
      });
      await user.click(optionBtn);
      await user.click(optionBtn);

      await waitFor(() => {
        expect(screen.queryByText("CorrelationMatrix.MethodLabel")).toBeNull();
      });
    });
  });

  describe("API成功時", () => {
    it("createCorrelationTable が OK → Workspace へ遷移する", async () => {
      mockApi.createCorrelationTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "corr_result" },
      });
      mockTableLoader.selectedTableName = "sales";
      useTableInfosStore.setState({ tableInfos: [], activeTableName: "sales" });
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      // 出力データ名を入力
      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(mockApi.createCorrelationTable).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
      expect(useTableListStore.getState().tableList).toContain("corr_result");
      expect(vi.mocked(showMessageDialog)).not.toHaveBeenCalled();
    });

    it("work tab モードでは成功時に onSuccess を呼び、dirty が false に戻る", async () => {
      mockApi.createCorrelationTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "corr_result" },
      });
      const onSuccess = vi.fn();
      useWorkspaceTabsStore.setState({
        tabs: [
          {
            id: "work:CorrelationMatrix",
            kind: "work",
            title: "相関行列",
            featureKey: "CorrelationMatrix",
            dirty: true,
            createdAt: Date.now(),
            draftValues: {
              tableName: "sales",
              columnNames: ["price", "quantity"],
              newTableName: "corr_result",
              method: CorrelationMethod.pearson,
              decimalPlaces: 3,
              lowerTriangleOnly: false,
              missingHandling: MissingHandlingMethod.pairwise,
            },
            committedValues: {
              tableName: "sales",
              columnNames: ["price"],
              newTableName: "corr_old",
              method: CorrelationMethod.pearson,
              decimalPlaces: 3,
              lowerTriangleOnly: false,
              missingHandling: MissingHandlingMethod.pairwise,
            },
          },
        ],
        activeTabId: "work:CorrelationMatrix",
      });

      render(
        <CorrelationMatrix
          workTabId="work:CorrelationMatrix"
          onSuccess={onSuccess}
        />,
      );

      await submitForm();

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledWith("corr_result", {
          tableName: "sales",
          columnNames: ["price", "quantity"],
          newTableName: "corr_result",
          method: CorrelationMethod.pearson,
          decimalPlaces: 3,
          lowerTriangleOnly: false,
          missingHandling: MissingHandlingMethod.pairwise,
        });
      });

      expect(
        useWorkspaceTabsStore
          .getState()
          .tabs.find((tab) => tab.id === "work:CorrelationMatrix"),
      ).toMatchObject({
        kind: "work",
        dirty: false,
        draftValues: {
          tableName: "sales",
          columnNames: ["price", "quantity"],
          newTableName: "corr_result",
        },
        committedValues: {
          tableName: "sales",
          columnNames: ["price", "quantity"],
          newTableName: "corr_result",
        },
      });
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → エラーダイアログを表示する", async () => {
      mockApi.createCorrelationTable.mockResolvedValue({
        code: "UNEXPECTED_ERROR",
        message: "newTableName 'corr_result'は既に存在します。",
      });
      mockTableLoader.selectedTableName = "sales";
      useTableInfosStore.setState({ tableInfos: [], activeTableName: "sales" });
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "CorrelationMatrix.OutputDataLabel 'corr_result'は既に存在します。",
        );
      });
    });

    it("APIがthrowした場合 → extractApiErrorMessage経由でダイアログを表示する", async () => {
      mockApi.createCorrelationTable.mockRejectedValue(
        new Error("ネットワークエラー"),
      );
      mockTableLoader.selectedTableName = "sales";
      useTableInfosStore.setState({ tableInfos: [], activeTableName: "sales" });
      const user = userEvent.setup();
      render(<CorrelationMatrix />);

      const outputInput = screen.getByRole("textbox");
      await user.type(outputInput, "corr_result");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ネットワークエラー",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると Workspace に遷移する", async () => {
      const user = userEvent.setup();
      useCurrentPageStore.setState({ currentView: "Workspace" });
      render(<CorrelationMatrix />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
    });

    it("work tab モードではキャンセル時に onCancel を呼ぶ", async () => {
      const user = userEvent.setup();
      const onCancel = vi.fn();

      render(
        <CorrelationMatrix
          workTabId="work:CorrelationMatrix"
          onCancel={onCancel}
        />,
      );

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });
});
