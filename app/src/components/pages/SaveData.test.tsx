import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../../api/endpoints";
import { showConfirmDialog } from "../../lib/dialog/confirm";
import { showMessageDialog } from "../../lib/dialog/message";
import { useCurrentPageStore } from "../../stores/currentView";
import { useFilesStore } from "../../stores/files";
import { useSettingsStore } from "../../stores/settings";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import { SaveData } from "./SaveData";

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
vi.mock("../../lib/dialog/confirm", () => ({
  showConfirmDialog: vi.fn().mockResolvedValue(true),
}));

// checkFileExists / getFiles / getFilesSafe をすべてモック (Tauri bridge)
vi.mock("../../api/bridge/tauri-commands", () => ({
  checkFileExists: vi.fn().mockResolvedValue(false),
  getFiles: vi.fn().mockResolvedValue({ directoryPath: "/tmp", files: [] }),
  getFilesSafe: vi.fn().mockResolvedValue({ directoryPath: "", files: [] }),
}));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const mockApi = {
  exportFile: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getEconomiconAppAPI).mockReturnValue(mockApi as never);
  useTableListStore.setState({ tableList: ["sales", "costs"] });
  useTableInfosStore.setState({
    tableInfos: [
      {
        tableName: "sales",
        columnList: [{ name: "price", type: "Float64" }],
        totalRows: 10,
        isActive: true,
      },
    ],
    activeTableName: "sales",
  });
  useFilesStore.setState({ files: [], directoryPath: "" });
  useSettingsStore.setState({
    osName: "Windows",
    pathSeparator: "\\",
  } as never);
  useCurrentPageStore.setState({ currentView: "SaveData" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("SaveData コンポーネント", () => {
  describe("テーブルがある場合", () => {
    it("ファイル設定セクションが表示される", () => {
      render(<SaveData />);
      expect(screen.getByText("SaveDataView.FileSettings")).toBeInTheDocument();
    });

    it("テーブルなし時はキャンセルのみ表示される", () => {
      useTableListStore.setState({ tableList: [] });
      render(<SaveData />);
      expect(
        screen.getByRole("button", { name: "Common.Cancel" }),
      ).toBeInTheDocument();
      expect(screen.queryByText("SaveDataView.FileSettings")).toBeNull();
    });
  });

  describe("バリデーション", () => {
    it("テーブル名とファイル名が空の時は保存できない", async () => {
      const user = userEvent.setup();
      // activeTableName を null にしてデフォルト値を空にする
      useTableInfosStore.setState({
        tableInfos: [],
        activeTableName: null,
      });
      render(<SaveData />);

      // テーブル名を空にする（初期状態で activeTableName=null なので空）
      // ファイル名フィールドを空にする
      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      // すでに空の状態で保存ボタンをクリック
      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(
          screen.getByText("ValidationMessages.DataNameRequired"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("上書き確認", () => {
    it("既存ファイルあり + 確認でキャンセル → 保存されない", async () => {
      const { checkFileExists } =
        await import("../../api/bridge/tauri-commands");
      vi.mocked(checkFileExists).mockResolvedValue(true);
      vi.mocked(showConfirmDialog).mockResolvedValue(false);

      const user = userEvent.setup();
      render(<SaveData />);

      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      await user.clear(fileNameInput);
      await user.type(fileNameInput, "output");

      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(vi.mocked(showConfirmDialog)).toHaveBeenCalled();
      });
      expect(mockApi.exportFile).not.toHaveBeenCalled();
    });

    it("既存ファイルあり + 確認でOK → exportFile を呼ぶ", async () => {
      const { checkFileExists } =
        await import("../../api/bridge/tauri-commands");
      vi.mocked(checkFileExists).mockResolvedValue(true);
      vi.mocked(showConfirmDialog).mockResolvedValue(true);
      mockApi.exportFile.mockResolvedValue({
        code: "OK",
        result: { filePath: "/tmp/output.csv" },
      });

      const user = userEvent.setup();
      render(<SaveData />);

      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      await user.clear(fileNameInput);
      await user.type(fileNameInput, "output");

      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(mockApi.exportFile).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("API成功時", () => {
    it("exportFile が OK → 成功ダイアログ表示 → DataPreview に遷移する", async () => {
      mockApi.exportFile.mockResolvedValue({
        code: "OK",
        result: { filePath: "/tmp/output.csv" },
      });
      const user = userEvent.setup();
      render(<SaveData />);

      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      await user.clear(fileNameInput);
      await user.type(fileNameInput, "output");

      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Common.OK",
          expect.stringContaining("SaveDataView.SaveSuccess"),
        );
      });
      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });

  describe("API失敗時", () => {
    it("code ≠ OK → エラーダイアログを表示する", async () => {
      mockApi.exportFile.mockResolvedValue({
        code: "UNEXPECTED_ERROR",
        message: "保存失敗",
      });
      const user = userEvent.setup();
      render(<SaveData />);

      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      await user.clear(fileNameInput);
      await user.type(fileNameInput, "output");

      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          expect.any(String),
        );
      });
    });

    it("APIがthrowした場合 → extractApiErrorMessage 経由でダイアログを表示する", async () => {
      mockApi.exportFile.mockRejectedValue(new Error("ディスクエラー"));
      const user = userEvent.setup();
      render(<SaveData />);

      const fileNameInput = screen.getByPlaceholderText(/FileName|ファイル名/i);
      await user.clear(fileNameInput);
      await user.type(fileNameInput, "output");

      const saveBtn = screen.getByRole("button", {
        name: /SaveDataView.Save/i,
      });
      await user.click(saveBtn);

      await waitFor(() => {
        expect(vi.mocked(showMessageDialog)).toHaveBeenCalledWith(
          "Error.Error",
          "ディスクエラー",
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<SaveData />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });

    it("テーブルなし時のキャンセルは ImportDataFile に遷移する", async () => {
      useTableListStore.setState({ tableList: [] });
      const user = userEvent.setup();
      render(<SaveData />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });
  });
});
