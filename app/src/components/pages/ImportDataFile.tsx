import * as RadixTabs from "@radix-ui/react-tabs";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  getFiles,
  getFilesSafe,
  TauriFileError,
} from "../../api/bridge/tauri-commands";
import { getEconomiconAPI } from "../../api/endpoints";
import { showMessageDialog } from "../../lib/dialog/message";
import type { ImportConfigSettings } from "../../lib/utils/importSchema";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useFilesStore } from "../../stores/files";
import { useLoadingStore } from "../../stores/loading";
import { useSettingsStore } from "../../stores/settings";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import type {
  FileType,
  SortDirection,
  SortField,
} from "../../types/commonTypes";
import { CancelButtonBar } from "../molecules/ActionBar/CancelButtonBar";
import { NavigationSearchBar } from "../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../molecules/Table/FileListTable";
import { ImportConfigDialog } from "../organisms/Dialog/ImportConfigDialog";
import { PageLayout } from "../templates/PageLayout";

type FileTypeFilter = "all" | "csv" | "excel" | "parquet";

const SUPPORTED_IMPORT_EXTENSIONS = [".csv", ".xlsx", ".xls", ".parquet"];

const FILE_TYPE_FILTERS: {
  value: FileTypeFilter;
  labelKey: string;
  extensions: string[];
}[] = [
  { value: "all", labelKey: "ImportDataFileView.AllFiles", extensions: [] },
  {
    value: "csv",
    labelKey: "ImportDataFileView.CsvFiles",
    extensions: [".csv"],
  },
  {
    value: "excel",
    labelKey: "ImportDataFileView.ExcelFiles",
    extensions: [".xlsx", ".xls"],
  },
  {
    value: "parquet",
    labelKey: "ImportDataFileView.ParquetFiles",
    extensions: [".parquet"],
  },
];

export const ImportDataFile = () => {
  const { t } = useTranslation();
  const osName = useSettingsStore((state) => state.osName);
  const pathSeparator = useSettingsStore((state) => state.pathSeparator);
  const files = useFilesStore((state) => state.files);
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const addTableList = useTableListStore((state) => state.addTableName);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

  const { setLoading, clearLoading } = useLoadingStore();

  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [fileTypeFilter, setFileTypeFilter] = useState<FileTypeFilter>("all");

  // Dialog State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState<{
    path: string;
    name: string;
  } | null>(null);

  // Tauri 2 ネイティブ drag-drop イベント
  const [isDragActive, setIsDragActive] = useState(false);

  useEffect(() => {
    let cleanup: (() => void) | undefined;

    getCurrentWindow()
      .onDragDropEvent((event) => {
        const type = event.payload.type;
        if (type === "enter" || type === "over") {
          setIsDragActive(true);
        } else if (type === "leave") {
          setIsDragActive(false);
        } else if (type === "drop") {
          setIsDragActive(false);
          const paths = "paths" in event.payload ? event.payload.paths : [];
          if (paths.length > 0) {
            const filePath = paths[0];
            const fileName =
              filePath.replace(/\\/g, "/").split("/").pop() ?? filePath;
            const ext = fileName.toLowerCase().match(/\.[^.]+$/)?.[0] ?? "";
            if (SUPPORTED_IMPORT_EXTENSIONS.includes(ext)) {
              setSelectedFileInfo({ path: filePath, name: fileName });
              setIsImportDialogOpen(true);
            }
          }
        }
      })
      .then((unlisten) => {
        cleanup = unlisten;
      });

    return () => {
      cleanup?.();
    };
  }, []);

  // ファイルパスを分割するヘルパー関数
  const getPathSegments = () => {
    if (!directoryPath) return [];
    return directoryPath
      .split(pathSeparator)
      .filter((segment) => segment.length > 0);
  };

  // 指定したインデックスまでのパスを構築するヘルパー関数
  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    if (index < 0) return pathSeparator;
    const selectedSegments = segments.slice(0, index + 1);
    const basePath = selectedSegments.join(pathSeparator);
    return osName === "Windows" ? basePath + pathSeparator : "/" + basePath;
  };

  // ディレクトリ変更処理
  const changeDirectory = async (newPath: string) => {
    // delay: 200ms — 一瞬で完了した場合はローディングを表示しない
    setLoading(true, t("Loading.Loading"), 200);
    try {
      const result = await getFiles(newPath);
      setFiles(result);
    } catch (e: unknown) {
      if (e instanceof TauriFileError && e.errorType === "PathNotFound") {
        // フォルダが削除されていた場合：専用メッセージを表示し、現在ディレクトリを再読み込み
        await showMessageDialog(t("Error.Error"), t("Error.DirectoryNotFound"));
        // 現在地そのものが有効な場合はリストを更新して削除済エントリを除去
        if (directoryPath) {
          try {
            const refreshed = await getFiles(directoryPath);
            setFiles(refreshed);
          } catch {
            // 現在地も消えている場合はホームディレクトリへフォールバック
            const safeFiles = await getFilesSafe("");
            setFiles(safeFiles);
          }
        }
      } else {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      }
    } finally {
      clearLoading();
    }
  };

  // 上位ディレクトリへ移動
  const goUpDirectory = async () => {
    const segments = getPathSegments();
    if (segments.length > 0) {
      const parentPath = buildPathUpToIndex(segments.length - 2);
      await changeDirectory(parentPath);
    }
  };

  // パンくずリストクリック処理
  const handleBreadcrumbClick = async (index: number) => {
    const targetPath = buildPathUpToIndex(index);
    await changeDirectory(targetPath);
  };

  // ファイルクリック処理
  const handleFileClick = async (file: FileType) => {
    if (!file.isFile) {
      const newPath =
        directoryPath === pathSeparator
          ? pathSeparator + file.name
          : directoryPath + pathSeparator + file.name;
      await changeDirectory(newPath);
    } else {
      setSelectedFileInfo({
        path: directoryPath + pathSeparator + file.name,
        name: file.name,
      });
      setIsImportDialogOpen(true);
    }
  };

  const executeImport = async (settings: ImportConfigSettings) => {
    if (!selectedFileInfo) return;

    setLoading(true, t("Loading.Loading"));
    try {
      let loadTableName = "";
      const { path } = selectedFileInfo;

      // 新APIは拡張子を自動判定し、CSV/Excel/Parquetを共用の1エンドポイントで処理
      const response = await getEconomiconAPI().importFile({
        filePath: path,
        tableName: settings.tableName,
        separator: settings.separator,
        sheetName: settings.sheetName,
        encoding: settings.encoding as
          | "utf8"
          | "latin1"
          | "ascii"
          | "gbk"
          | "windows-1252"
          | "shift_jis"
          | undefined,
      });

      if (response && response.code !== "OK") {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        return;
      }

      if (response) {
        loadTableName = response.result.tableName;
        const resTableInfo = await getTableInfo(loadTableName);
        addTableList(loadTableName);
        addTableInfo(resTableInfo);
        setCurrentView("DataPreview");
      }
    } catch (e: unknown) {
      console.error(e);
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
    } finally {
      clearLoading();
    }
  };

  const filteredFiles = files
    .filter((file) =>
      file.name.toLowerCase().includes(searchValue.toLowerCase()),
    )
    .filter((file) => {
      // フォルダは常に表示
      if (!file.isFile) return true;
      if (fileTypeFilter === "all") return true;
      const filterDef = FILE_TYPE_FILTERS.find(
        (f) => f.value === fileTypeFilter,
      );
      if (!filterDef) return true;
      const lower = file.name.toLowerCase();
      return filterDef.extensions.some((ext) => lower.endsWith(ext));
    });

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    if (!sortField || !sortDirection) return 0;
    if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
    let aValue: string | number = "";
    let bValue: string | number = "";
    switch (sortField) {
      case "name":
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case "size":
        aValue = a.isFile ? a.size || 0 : 0;
        bValue = b.isFile ? b.size || 0 : 0;
        break;
      case "modifiedTime":
        aValue = a.isFile ? new Date(a.modifiedTime).getTime() : 0;
        bValue = b.isFile ? new Date(b.modifiedTime).getTime() : 0;
        break;
    }
    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1;
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1;
    return 0;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(
        sortDirection === "asc"
          ? "desc"
          : sortDirection === "desc"
            ? null
            : "asc",
      );
      if (sortDirection === "desc") setSortField(null);
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleCancel = () => setCurrentView("DataPreview");

  return (
    <PageLayout
      title={t("ImportDataFileView.Title")}
      description={t("ImportDataFileView.Description")}
    >
      <ImportConfigDialog
        isOpen={isImportDialogOpen}
        onOpenChange={setIsImportDialogOpen}
        fileInfo={selectedFileInfo}
        onImport={executeImport}
      />

      <RadixTabs.Root
        defaultValue="dragDrop"
        className="flex flex-1 flex-col gap-2 min-h-0"
      >
        <RadixTabs.List className="flex w-full border-b border-gray-200">
          <RadixTabs.Trigger
            value="dragDrop"
            className="group relative flex h-9 items-center justify-center px-4 text-sm font-medium text-gray-500 hover:text-gray-700 data-[state=active]:font-semibold data-[state=active]:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
          >
            {t("ImportDataFileView.DragAndDropTab")}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
          <RadixTabs.Trigger
            value="fileSelect"
            className="group relative flex h-9 items-center justify-center px-4 text-sm font-medium text-gray-500 hover:text-gray-700 data-[state=active]:font-semibold data-[state=active]:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
          >
            {t("ImportDataFileView.FileSelectTab")}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
        </RadixTabs.List>

        <RadixTabs.Content value="dragDrop" className="shrink-0 outline-none">
          <div
            className={`flex h-56 w-full flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
              isDragActive
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 hover:border-gray-400 bg-gray-50"
            }`}
          >
            <UploadCloud
              className={`mb-4 h-16 w-16 ${
                isDragActive ? "text-blue-500" : "text-gray-400"
              }`}
            />
            <h3 className="mb-2 text-lg font-semibold text-gray-700">
              {isDragActive
                ? t("ImportDataFileView.DragDropAreaTitleActive")
                : t("ImportDataFileView.DragDropAreaTitle")}
            </h3>
            <p className="text-sm text-gray-500">
              {t("ImportDataFileView.DragDropAreaDescription")}
            </p>
          </div>
        </RadixTabs.Content>

        <RadixTabs.Content
          value="fileSelect"
          className="flex flex-1 flex-col gap-2 min-h-0 outline-none"
        >
          <NavigationSearchBar
            pathSegments={getPathSegments()}
            searchValue={searchValue}
            searchPlaceholder={t("ImportDataFileView.SearchPlaceholder")}
            upDirectoryTitle={t("ImportDataFileView.GoUpDirectory")}
            onUpDirectory={goUpDirectory}
            onBreadcrumbClick={handleBreadcrumbClick}
            onSearchChange={setSearchValue}
          />

          {/* ファイル種類フィルター ToggleGroup */}
          <ToggleGroup.Root
            type="single"
            value={fileTypeFilter}
            onValueChange={(v) => v && setFileTypeFilter(v as FileTypeFilter)}
            className="flex shrink-0 flex-wrap gap-1.5"
            aria-label={t("ImportDataFileView.FileTypeFilterLabel")}
          >
            {FILE_TYPE_FILTERS.map((filter) => (
              <ToggleGroup.Item
                key={filter.value}
                value={filter.value}
                className="rounded-full border px-3 py-0.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/50 data-[state=on]:border-brand-primary data-[state=on]:bg-brand-primary data-[state=on]:text-white data-[state=off]:border-gray-300 data-[state=off]:bg-white data-[state=off]:text-gray-600 data-[state=off]:hover:border-brand-primary/50 data-[state=off]:hover:bg-brand-primary/5"
              >
                {t(filter.labelKey)}
              </ToggleGroup.Item>
            ))}
          </ToggleGroup.Root>

          <FileListTable
            files={sortedFiles}
            onFileClick={handleFileClick}
            fileNameHeader={t("ImportDataFileView.FileNameHeader")}
            sizeHeader={t("ImportDataFileView.SizeHeader")}
            lastModifiedHeader={t("ImportDataFileView.LastModifiedHeader")}
            maxHeight="100%"
            className="flex-1 min-h-0"
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        </RadixTabs.Content>
      </RadixTabs.Root>

      <CancelButtonBar
        cancelText={t("Common.Cancel")}
        onCancel={handleCancel}
      />
    </PageLayout>
  );
};
