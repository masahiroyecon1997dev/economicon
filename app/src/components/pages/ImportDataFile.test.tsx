import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getFiles } from "../../api/bridge/tauri-commands";
import { useCurrentPageStore } from "../../stores/currentView";
import { useFilesStore } from "../../stores/files";
import { useSettingsStore } from "../../stores/settings";
import { ImportDataFile } from "./ImportDataFile";

const { mockFileListTable } = vi.hoisted(() => ({
  mockFileListTable: vi.fn(),
}));

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

vi.mock("../../api/bridge/tauri-commands", () => ({
  getFiles: vi.fn().mockResolvedValue({ directoryPath: "/tmp", files: [] }),
  getFilesSafe: vi.fn().mockResolvedValue({ directoryPath: "", files: [] }),
  TauriFileError: class TauriFileError extends Error {
    errorType: string;
    originalMessage: string;
    constructor(errorType: string, originalMessage: string) {
      super(originalMessage);
      this.errorType = errorType;
      this.originalMessage = originalMessage;
      this.name = "TauriFileError";
    }
  },
}));

// Tauri ウィンドウ drag-drop イベントのモック
vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: () => ({
    onDragDropEvent: vi.fn().mockResolvedValue(() => {}),
  }),
}));

// ImportConfigDialog は複合コンポーネントなのでスタブ化
vi.mock("../organisms/Dialog/ImportConfigDialog", () => ({
  ImportConfigDialog: () => <div data-testid="import-config-dialog" />,
}));
vi.mock("../molecules/Table/FileListTable", () => ({
  FileListTable: (props: { files: Array<{ name: string }> }) => {
    mockFileListTable(props);
    return (
      <div data-testid="file-list-table">
        {props.files.map((file) => (
          <div key={file.name}>{file.name}</div>
        ))}
      </div>
    );
  },
}));

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
beforeEach(() => {
  vi.clearAllMocks();
  useFilesStore.setState({ files: [], directoryPath: "" });
  useSettingsStore.setState({
    osName: "Windows",
    pathSeparator: "\\",
  } as never);
  useCurrentPageStore.setState({ currentView: "ImportDataFile" });
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("ImportDataFile コンポーネント", () => {
  describe("初期レンダリング", () => {
    it("タイトルが表示される", () => {
      render(<ImportDataFile />);
      expect(screen.getByText("ImportDataFileView.Title")).toBeInTheDocument();
    });

    it("ドラッグ&ドロップタブとファイル選択タブが表示される", () => {
      render(<ImportDataFile />);
      expect(
        screen.getByText("ImportDataFileView.DragAndDropTab"),
      ).toBeInTheDocument();
      expect(
        screen.getByText("ImportDataFileView.FileSelectTab"),
      ).toBeInTheDocument();
    });

    it("ドラッグ&ドロップエリアのタイトルが表示される", () => {
      render(<ImportDataFile />);
      expect(
        screen.getByText("ImportDataFileView.DragDropAreaTitle"),
      ).toBeInTheDocument();
    });
  });

  describe("タブ切替", () => {
    it("ファイル選択タブをクリックするとファイルフィルターが表示される", async () => {
      const user = userEvent.setup();
      render(<ImportDataFile />);

      const fileSelectTab = screen.getByText(
        "ImportDataFileView.FileSelectTab",
      );
      await user.click(fileSelectTab);

      await waitFor(() => {
        expect(
          screen.getByText("ImportDataFileView.AllFiles"),
        ).toBeInTheDocument();
      });
    });

    it("ファイル選択タブでCSVフィルターが表示される", async () => {
      const user = userEvent.setup();
      render(<ImportDataFile />);

      const fileSelectTab = screen.getByText(
        "ImportDataFileView.FileSelectTab",
      );
      await user.click(fileSelectTab);

      await waitFor(() => {
        expect(
          screen.getByText("ImportDataFileView.CsvFiles"),
        ).toBeInTheDocument();
        expect(
          screen.getByText("ImportDataFileView.ExcelFiles"),
        ).toBeInTheDocument();
        expect(
          screen.getByText("ImportDataFileView.ParquetFiles"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("ファイルリスト", () => {
    it("ファイルがある場合はファイル名が表示される", async () => {
      vi.mocked(getFiles).mockResolvedValue({
        directoryPath: "/tmp",
        files: [
          {
            name: "test.csv",
            isFile: true,
            size: 1024,
            modifiedTime: new Date().toISOString(),
          },
        ],
      });
      useFilesStore.setState({
        files: [
          {
            name: "test.csv",
            isFile: true,
            size: 1024,
            modifiedTime: new Date().toISOString(),
          },
        ],
        directoryPath: "/tmp",
      });

      const user = userEvent.setup();
      render(<ImportDataFile />);

      const fileSelectTab = screen.getByText(
        "ImportDataFileView.FileSelectTab",
      );
      await user.click(fileSelectTab);

      await waitFor(() => {
        expect(mockFileListTable).toHaveBeenCalled();
        expect(mockFileListTable.mock.calls.at(-1)?.[0].files).toEqual(
          expect.arrayContaining([
            expect.objectContaining({ name: "test.csv" }),
          ]),
        );
      });
    });
  });

  describe("キャンセル", () => {
    it("キャンセルボタンをクリックすると DataPreview に遷移する", async () => {
      const user = userEvent.setup();
      render(<ImportDataFile />);

      const cancelBtn = screen.getByRole("button", { name: "Common.Cancel" });
      await user.click(cancelBtn);

      expect(useCurrentPageStore.getState().currentView).toBe("DataPreview");
    });
  });
});
