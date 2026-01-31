import * as RadixTabs from '@radix-ui/react-tabs';
import { listen } from "@tauri-apps/api/event";
import { UploadCloud } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getTableInfo } from "../../../functions/internalFunctions";
import { showMessageDialog } from "../../../functions/messageDialog";
import { getFiles, importCsvByPath, importExcelByPath, importParquetByPath } from "../../../functions/restApis";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useFilesStore } from "../../../stores/useFilesStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { FileType, SortDirection, SortField } from "../../../types/commonTypes";
import { CancelButtonBar } from "../../molecules/ActionBar/CancelButtonBar";
import { NavigationSearchBar } from "../../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../../molecules/Table/FileListTable";
import { ImportConfigDialog } from "../../organisms/Modal/ImportConfigDialog";
import { MainViewLayout } from "../Layouts/MainViewLayout";

interface DropEvent {
  payload: {
    paths: string[];
  };
}

export const ImportDataFileView = () => {
  const { t } = useTranslation();
  const files = useFilesStore((state) => state.files);
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const osName = useSettingsStore((state) => state.osName);
  const pathSeparator = useSettingsStore((state) => state.pathSeparator);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const addTableList = useTableListStore((state) => state.addTableName);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const { setLoading, clearLoading } = useLoadingStore();

  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  // Dialog State
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const [selectedFileInfo, setSelectedFileInfo] = useState<{ path: string; name: string } | null>(null);

  // Tauri Drop Event Listener
  useEffect(() => {
    let unlisten: () => void;

    const setupListener = async () => {
      unlisten = await listen('tauri://drop', (event: DropEvent) => {
        if (event.payload.paths && event.payload.paths.length > 0) {
          const path = event.payload.paths[0];
          // ファイル名を取得する簡易ロジック
          const name = path.split(/[/\\]/).pop() || path;
          setSelectedFileInfo({ path, name });
          setIsImportDialogOpen(true);
        }
      });
    };

    setupListener();

    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  // HTML5 Drag & Drop (Mainly for UI indication, actual drop handled by Tauri event or below)
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    // Note: React's onDrop gives File objects. File.path might be available in Tauri.
    // However, we rely on tauri://drop listener primarily for path accuracy.
    // If tauri://drop doesn't fire for some reason (e.g. not configured), we can fallback:
    /*
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
        // (droppedFiles[0] as any).path logic
    }
    */
  };


  const getPathSegments = () => {
    if (!directoryPath) return [];
    const separator = pathSeparator || "/";
    return directoryPath.split(separator).filter((segment) => segment.length > 0);
  };

  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    const separator = pathSeparator || "/";
    if (index < 0) return separator;
    const selectedSegments = segments.slice(0, index + 1);
    let path = selectedSegments.join(separator);
    if (osName === "Windows") path += separator;
    else if (separator === "/") path = "/" + path;
    return path;
  };

  const changeDirectory = async (newPath: string) => {
    setLoading(true, t("Loading.Loading"));
    try {
      const response = await getFiles(newPath);
      if (response.code === "OK") setFiles(response.result);
      else await showMessageDialog(t("Error.Error"), response.message);
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
    } finally {
      clearLoading();
    }
  };

  const goUpDirectory = async () => {
    const segments = getPathSegments();
    if (segments.length > 0) {
      const parentPath = buildPathUpToIndex(segments.length - 2);
      await changeDirectory(parentPath);
    }
  };

  const handleBreadcrumbClick = async (index: number) => {
    const targetPath = buildPathUpToIndex(index);
    await changeDirectory(targetPath);
  };

  const handleFileClick = async (file: FileType) => {
    if (!file.isFile) {
      const separator = pathSeparator || "/";
      const newPath =
        directoryPath === separator
          ? separator + file.name
          : directoryPath + separator + file.name;
      setLoading(true, t("Loading.Loading"));
      try {
        const response = await getFiles(newPath);
        if (response.code === "OK") setFiles(response.result);
        else await showMessageDialog(t("Error.Error"), response.message);
      } catch {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } finally {
        clearLoading();
      }
    } else {
      // Instead of importing immediately, open dialog
      setSelectedFileInfo({
        path: directoryPath + (pathSeparator || '/') + file.name,
        name: file.name
      });
      setIsImportDialogOpen(true);
    }
  };

  const executeImport = async (settings: { tableName: string; sheetName?: string; separator?: string }) => {
    if (!selectedFileInfo) return;

    setLoading(true, t("Loading.Loading"));
    try {
      let loadTableName = '';
      const { path, name } = selectedFileInfo;
      let response;
      const lowerName = name.toLowerCase();

      if (lowerName.endsWith('.csv')) {
        response = await importCsvByPath({
          filePath: path,
          tableName: settings.tableName,
          separator: settings.separator || ',',
        });
      } else if (lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls')) {
        response = await importExcelByPath({
          filePath: path,
          tableName: settings.tableName,
          sheetName: settings.sheetName || '',
        });
      } else if (lowerName.endsWith('.parquet')) {
        response = await importParquetByPath({
          filePath: path,
          tableName: settings.tableName,
        });
      } else {
        await showMessageDialog(t('Error.Error'), t('SelectFileView.UnsupportedFileType'));
        return;
      }

      if (response && response.code !== "OK") {
        await showMessageDialog(t('Error.Error'), response.message);
        return;
      }

      if (response) {
        loadTableName = response.result.tableName;
        const resTableInfo = await getTableInfo(loadTableName);
        addTableList(loadTableName);
        addTableInfo(resTableInfo);
        setCurrentView("DataPreview");
      }

    } catch (e: any) {
      console.error(e);
      await showMessageDialog(t('Error.Error'), t('Error.UnexpectedError'));
    } finally {
      clearLoading();
    }
  };


  const filteredFiles = files.filter((file) =>
    file.name.toLowerCase().includes(searchValue.toLowerCase())
  );

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
      setSortDirection(sortDirection === "asc" ? "desc" : sortDirection === "desc" ? null : "asc");
      if (sortDirection === "desc") setSortField(null);
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleCancel = () => setCurrentView("DataPreview");

  return (
    <MainViewLayout
      title={t("SelectFileView.Title")}
      description={t("SelectFileView.Description")}
    >
      <ImportConfigDialog
        isOpen={isImportDialogOpen}
        onOpenChange={setIsImportDialogOpen}
        fileInfo={selectedFileInfo}
        onImport={executeImport}
      />

      <RadixTabs.Root defaultValue="dragDrop" className="flex w-full flex-col gap-4">
        <RadixTabs.List className="flex w-full border-b border-gray-200">
          <RadixTabs.Trigger
            value="dragDrop"
            className="group relative flex h-9 items-center justify-center px-4 text-sm font-medium text-gray-500 hover:text-gray-700 data-[state=active]:font-semibold data-[state=active]:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
          >
            {t('SelectFileView.DragAndDropTab')}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
          <RadixTabs.Trigger
            value="fileSelect"
            className="group relative flex h-9 items-center justify-center px-4 text-sm font-medium text-gray-500 hover:text-gray-700 data-[state=active]:font-semibold data-[state=active]:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
          >
            {t('SelectFileView.FileSelectTab')}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
        </RadixTabs.List>

        <RadixTabs.Content value="dragDrop" className="flex-1 outline-none">
          <div
            className={`flex h-[400px] w-full flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${isDragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400 bg-gray-50"
              }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <UploadCloud className={`mb-4 h-16 w-16 ${isDragOver ? "text-blue-500" : "text-gray-400"}`} />
            <h3 className="mb-2 text-lg font-semibold text-gray-700">
              {t('SelectFileView.DragDropAreaTitle')}
            </h3>
            <p className="text-sm text-gray-500">
              {t('SelectFileView.DragDropAreaDescription')}
            </p>
          </div>
        </RadixTabs.Content>

        <RadixTabs.Content value="fileSelect" className="flex flex-col gap-1.5 md:gap-3 shrink-0 outline-none">
          <NavigationSearchBar
            pathSegments={getPathSegments()}
            searchValue={searchValue}
            searchPlaceholder={t("SelectFileView.SearchPlaceholder")}
            upDirectoryTitle={t("SelectFileView.GoUpDirectory")}
            onUpDirectory={goUpDirectory}
            onBreadcrumbClick={handleBreadcrumbClick}
            onSearchChange={setSearchValue}
          />

          <FileListTable
            files={sortedFiles}
            onFileClick={handleFileClick}
            fileNameHeader={t("SelectFileView.FileNameHeader")}
            sizeHeader={t("SelectFileView.SizeHeader")}
            lastModifiedHeader={t("SelectFileView.LastModifiedHeader")}
            maxHeight="max(200px, calc(100vh - 350px))"
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
    </MainViewLayout>
  );
};
