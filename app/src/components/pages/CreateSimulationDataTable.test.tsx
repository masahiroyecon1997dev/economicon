import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act, beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import { CreateSimulationDataTable } from "./CreateSimulationDataTable";

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
    tableName: "sim_table",
    columnList: [],
    totalRows: 0,
    isActive: true,
  }),
}));
vi.mock("../organisms/Dialog/SimulationColumnEditDialog", () => ({
  SimulationColumnEditDialog: () => (
    <div data-testid="sim-column-edit-dialog" />
  ),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  createSimulationDataTable: vi.fn(),
};

const submitForm = async () => {
  await act(async () => {
    fireEvent.submit(document.querySelector("form")!);
  });
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: [] });
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  useCurrentPageStore.setState({ currentView: "CreateSimulationDataTable" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("CreateSimulationDataTable フォーム", () => {
  describe("初期レンダリング", () => {
    it("データ名・行数フィールドと列設定セクションが表示される", () => {
      render(<CreateSimulationDataTable />);

      expect(
        screen.getByText("CreateSimulationDataTableView.DataSettings"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("CreateSimulationDataTableView.ColumnSettings"),
      ).toBeInTheDocument();
    });

    it("初期状態で列が1行表示される", () => {
      render(<CreateSimulationDataTable />);
      // 列設定の行（Editアイコン + Deleteアイコン）が1セット存在する
      const editBtns = screen.getAllByRole("button", {
        name: /Edit|編集/i,
      });
      expect(editBtns).toHaveLength(1);
    });
  });

  describe("列の追加・削除", () => {
    it("列を追加ボタンをクリックすると列が増える", async () => {
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      const addBtn = screen.getByRole("button", {
        name: /AddColumn/,
      });
      await user.click(addBtn);
      await user.click(addBtn);

      const editBtns = screen.getAllByRole("button", {
        name: /Edit|編集/i,
      });
      expect(editBtns).toHaveLength(3);
    });

    it("削除ボタンをクリックすると列が減る", async () => {
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      // まず1列追加して2列にする
      const addBtn = screen.getByRole("button", { name: /AddColumn/ });
      await user.click(addBtn);

      const deleteBtns = screen.getAllByRole("button", {
        name: /Delete|削除/i,
      });
      expect(deleteBtns).toHaveLength(2);
      await user.click(deleteBtns[0]);

      await waitFor(() => {
        const afterDelete = screen.getAllByRole("button", {
          name: /Delete|削除/i,
        });
        expect(afterDelete).toHaveLength(1);
      });
    });
  });

  describe("バリデーション", () => {
    it("データ名が空でサブミットするとバリデーションエラーが表示される", async () => {
      render(<CreateSimulationDataTable />);
      await submitForm();

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("API成功時", () => {
    it("createSimulationDataTable が OK → DataPreview に遷移する", async () => {
      mockApi.createSimulationDataTable.mockResolvedValue({
        code: "OK",
        result: { tableName: "sim_table" },
      });
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      const tableNameInput = screen.getByRole("textbox", {
        name: /DataName/,
      });
      await user.type(tableNameInput, "sim_table");

      await submitForm();

      await waitFor(() => {
        expect(mockApi.createSimulationDataTable).toHaveBeenCalledTimes(1);
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → DataCreationFailed ダイアログを表示する", async () => {
      mockApi.createSimulationDataTable.mockResolvedValue({
        code: "UNEXPECTED_ERROR",
        message: "作成失敗",
      });
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      const tableNameInput = screen.getByRole("textbox", { name: /DataName/ });
      await user.type(tableNameInput, "sim_table");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "CreateSimulationDataTableView.DataCreationFailed",
        );
      });
    });

    it("APIがthrowした場合 → error.message でダイアログを表示する", async () => {
      mockApi.createSimulationDataTable.mockRejectedValue(
        new Error("サーバーエラー"),
      );
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      const tableNameInput = screen.getByRole("textbox", { name: /DataName/ });
      await user.type(tableNameInput, "sim_table");

      await submitForm();

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "サーバーエラー",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると ImportDataFile に遷移する", async () => {
      const user = userEvent.setup();
      render(<CreateSimulationDataTable />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });
  });
});
