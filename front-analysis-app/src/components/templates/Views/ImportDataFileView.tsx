import * as RadixTabs from '@radix-ui/react-tabs';
import { UploadCloud } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from 'react-dropzone';
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


  // ドロップゾーンのonDropハンドラ
  const onDrop = useCallback((acceptedFiles: File[]) => {
    console.log("Dropped file path:");
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];

      // Tauri環境の場合、Fileオブジェクトに 'path' プロパティが含まれていることが一般的
      // 型定義にはないので any キャストを使用、または @types/react-dropzoneの内容を確認
      const filePath = (file as any).path;
      if (filePath) {

        setSelectedFileInfo({ path: filePath, name: file.name });
        setIsImportDialogOpen(true);
      } else {
        // ブラウザなどでpathが取れない場合のフォールバック（今回はTauri前提なのでエラー表示も検討）
        // TauriのWebViewでpathが取れない場合は、上記のtauri://dropを使うことになりますが、
        // react-dropzone経由でも通常はpathが取れます。
        console.warn("File path not found in dropped file object.");
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true, // クリックでファイル選択ダイアログを開かない（今回はD&D専用エリアとするため）
    multiple: false,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      // parquetはMIMEタイプが決まっていないことが多いので拡張子で
      'application/octet-stream': ['.parquet']
    }
  });


  // ファイルパスを分割するヘルパー関数
  const getPathSegments = () => {
    if (!directoryPath) return [];
    const separator = pathSeparator || "/";
    return directoryPath.split(separator).filter((segment) => segment.length > 0);
  };

  // 指定したインデックスまでのパスを構築するヘルパー関数
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

  // ディレクトリ変更処理
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
        await showMessageDialog(t('Error.Error'), t('ImportDataFileView.UnsupportedFileType'));
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
      title={t("ImportDataFileView.Title")}
      description={t("ImportDataFileView.Description")}
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
            {t('ImportDataFileView.DragAndDropTab')}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
          <RadixTabs.Trigger
            value="fileSelect"
            className="group relative flex h-9 items-center justify-center px-4 text-sm font-medium text-gray-500 hover:text-gray-700 data-[state=active]:font-semibold data-[state=active]:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950"
          >
            {t('ImportDataFileView.FileSelectTab')}
            <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 opacity-0 transition-opacity group-data-[state=active]:opacity-100" />
          </RadixTabs.Trigger>
        </RadixTabs.List>

        <RadixTabs.Content value="dragDrop" className="flex-1 outline-none">
          <div
            {...getRootProps()}
            className={`flex h-[400px] w-full flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400 bg-gray-50"
              }`}
          >
            <input {...getInputProps()} />
            <UploadCloud className={`mb-4 h-16 w-16 ${isDragActive ? "text-blue-500" : "text-gray-400"}`} />
            <h3 className="mb-2 text-lg font-semibold text-gray-700">
              {isDragActive ? t('ImportDataFileView.DragDropAreaTitleActive') : t('ImportDataFileView.DragDropAreaTitle')}
            </h3>
            <p className="text-sm text-gray-500">
              {t('ImportDataFileView.DragDropAreaDescription')}
            </p>
          </div>
        </RadixTabs.Content>

        <RadixTabs.Content value="fileSelect" className="flex flex-col gap-1.5 md:gap-3 shrink-0 outline-none">
          <NavigationSearchBar
            pathSegments={getPathSegments()}
            searchValue={searchValue}
            searchPlaceholder={t("ImportDataFileView.SearchPlaceholder")}
            upDirectoryTitle={t("ImportDataFileView.GoUpDirectory")}
            onUpDirectory={goUpDirectory}
            onBreadcrumbClick={handleBreadcrumbClick}
            onSearchChange={setSearchValue}
          />

          <FileListTable
            files={sortedFiles}
            onFileClick={handleFileClick}
            fileNameHeader={t("ImportDataFileView.FileNameHeader")}
            sizeHeader={t("ImportDataFileView.SizeHeader")}
            lastModifiedHeader={t("ImportDataFileView.LastModifiedHeader")}
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
