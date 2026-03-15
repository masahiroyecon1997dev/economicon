import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  checkFileExists,
  getFiles,
  getFilesSafe,
} from "../../api/bridge/tauri-commands";
import { getEconomiconAPI } from "../../api/endpoints";
import type { ExportFileRequestBodyFormat } from "../../api/model";
import { showConfirmDialog } from "../../lib/dialog/confirm";
import { showMessageDialog } from "../../lib/dialog/message";
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
import { InputText } from "../atoms/Input/InputText";
import { Select, SelectItem } from "../atoms/Input/Select";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { CancelButtonBar } from "../molecules/ActionBar/CancelButtonBar";
import { FormField } from "../molecules/Form/FormField";
import { NavigationSearchBar } from "../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../molecules/Table/FileListTable";
import { PageLayout } from "../templates/PageLayout";

type FileFormat = "csv" | "excel" | "parquet";

export const SaveData = () => {
  const { t } = useTranslation();
  const files = useFilesStore((state) => state.files);
  const directoryPath = useFilesStore((state) => state.directoryPath);
  const setFiles = useFilesStore((state) => state.setFiles);
  const osName = useSettingsStore((state) => state.osName);
  const pathSeparator = useSettingsStore((state) => state.pathSeparator);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const tableNameList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

  const { setLoading, clearLoading } = useLoadingStore();

  const [selectedTableName, setSelectedTableName] = useState(
    activeTableName || "",
  );
  const [fileName, setFileName] = useState(activeTableName || "");
  const [fileFormat, setFileFormat] = useState<FileFormat>("csv");
  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [errorMessage, setErrorMessage] = useState<{
    tableName?: string;
    fileName?: string;
  }>({});

  // マウント時にファイルリストを最新化（画面遷移で表示が古くならないよう）
  useEffect(() => {
    if (directoryPath) {
      getFiles(directoryPath)
        .then(setFiles)
        .catch(() => {});
    } else {
      getFilesSafe("")
        .then(setFiles)
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fileFormatOptions = [
    { value: "csv", label: "CSV (.csv)" },
    { value: "excel", label: "Excel (.xlsx)" },
    { value: "parquet", label: "Parquet (.parquet)" },
  ];

  const getPathSegments = () => {
    if (!directoryPath) return [];
    const separator = pathSeparator || "/";
    return directoryPath
      .split(separator)
      .filter((segment) => segment.length > 0);
  };

  const buildPathUpToIndex = (index: number) => {
    const segments = getPathSegments();
    const separator = pathSeparator || "/";

    if (index < 0) {
      return separator;
    }

    const selectedSegments = segments.slice(0, index + 1);
    let path = selectedSegments.join(separator);

    if (osName === "Windows") {
      path += separator;
    } else if (separator === "/") {
      path = "/" + path;
    }

    return path;
  };

  const changeDirectory = async (newPath: string) => {
    setLoading(true, t("Loading.Loading"));
    try {
      // getFilesはFilesTypeを直接返す（エラー時は例外をスロー）
      const files = await getFiles(newPath);
      setFiles(files);
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
      // フォルダクリック→ディレクトリ移動
      const separator = pathSeparator || "/";
      const newPath =
        directoryPath === separator
          ? separator + file.name
          : directoryPath + separator + file.name;

      setLoading(true, t("Loading.Loading"));
      try {
        // getFilesはFilesTypeを直接返す（エラー時は例外をスロー）
        const files = await getFiles(newPath);
        setFiles(files);
      } catch {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } finally {
        clearLoading();
      }
    } else {
      // ファイルクリック→拡張子なしのベース名を保存ファイル名にセット
      const dotIndex = file.name.lastIndexOf(".");
      const baseName = dotIndex > 0 ? file.name.slice(0, dotIndex) : file.name;
      const ext =
        dotIndex > 0 ? file.name.slice(dotIndex + 1).toLowerCase() : "";
      setFileName(baseName);
      // 拡張子がサポートファーマットなら fileFormat も連動
      if (ext === "csv") setFileFormat("csv");
      else if (ext === "xlsx" || ext === "xls") setFileFormat("excel");
      else if (ext === "parquet") setFileFormat("parquet");
    }
  };

  const validateInput = (): boolean => {
    const errors: { tableName?: string; fileName?: string } = {};

    if (!selectedTableName || selectedTableName.trim() === "") {
      errors.tableName = t("ValidationMessages.DataNameRequired");
    }

    if (!fileName || fileName.trim() === "") {
      errors.fileName = t("ValidationMessages.FileNameRequired");
    }

    setErrorMessage(errors);
    return Object.keys(errors).length === 0;
  };

  const getFileExtension = (): string => {
    switch (fileFormat) {
      case "csv":
        return ".csv";
      case "excel":
        return ".xlsx";
      case "parquet":
        return ".parquet";
      default:
        return "";
    }
  };

  const handleSave = async () => {
    if (!validateInput()) {
      return;
    }

    const fullFileName = fileName.endsWith(getFileExtension())
      ? fileName
      : fileName + getFileExtension();

    // 保存先ディレクトリの同名ファイルを Rust 経由でチェック
    const separator = pathSeparator || "/";
    const fullPath =
      directoryPath && directoryPath !== separator
        ? directoryPath + separator + fullFileName
        : (directoryPath || "") + fullFileName;

    const exists = await checkFileExists(fullPath);
    if (exists) {
      const confirmed = await showConfirmDialog(
        t("SaveDataView.OverwriteConfirmTitle"),
        t("SaveDataView.OverwriteConfirmMessage", { fileName: fullFileName }),
      );
      if (!confirmed) return;
    }

    setLoading(true, t("SaveDataView.SavingFile"));

    try {
      // formatマッピング（FileFormat → ExportFileRequestBodyFormat）
      const formatMap: Record<FileFormat, ExportFileRequestBodyFormat> = {
        csv: "csv",
        excel: "excel",
        parquet: "parquet",
      };

      const response = await getEconomiconAPI().exportFile({
        tableName: selectedTableName,
        directoryPath: directoryPath,
        fileName: fullFileName,
        format: formatMap[fileFormat],
        separator: fileFormat === "csv" ? "," : undefined,
        sheetName: fileFormat === "excel" ? "Sheet1" : undefined,
      });

      if (response.code === "OK") {
        await showMessageDialog(
          t("Common.OK"),
          t("SaveDataView.SaveSuccess", { path: response.result.filePath }),
        );
        setCurrentView("DataPreview");
        clearLoading();
      } else {
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      }
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
    } finally {
      clearLoading();
    }
  };

  const hadleCancelNoTables = async () => {
    setCurrentView("ImportDataFile");
  };

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const filteredFiles = files.filter((file) => {
    const matchesSearch = file.name
      .toLowerCase()
      .includes(searchValue.toLowerCase());
    return matchesSearch;
  });

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    if (!sortField || !sortDirection) return 0;

    if (a.isFile !== b.isFile) {
      return a.isFile ? 1 : -1;
    }

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

    if (aValue < bValue) {
      return sortDirection === "asc" ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === "asc" ? 1 : -1;
    }
    return 0;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      if (sortDirection === "asc") {
        setSortDirection("desc");
      } else if (sortDirection === "desc") {
        setSortField(null);
        setSortDirection(null);
      } else {
        setSortDirection("asc");
      }
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  return (
    <PageLayout
      title={t("SaveDataView.Title")}
      description={
        tableNameList.length === 0
          ? t("SaveDataView.NoDataImported")
          : t("SaveDataView.Description")
      }
    >
      {tableNameList.length === 0 ? (
        <div className="flex flex-col justify-center h-full gap-4">
          <CancelButtonBar
            cancelText={t("Common.Cancel")}
            onCancel={hadleCancelNoTables}
          />
        </div>
      ) : (
        <>
          <div className="flex flex-col gap-3 flex-1 min-h-0">
            <div className="flex flex-col gap-3 shrink-0">
              <h2 className="text-lg font-bold text-black">
                {t("SaveDataView.SelectDirectory")}
              </h2>
              <NavigationSearchBar
                pathSegments={getPathSegments()}
                searchValue={searchValue}
                searchPlaceholder={t("ImportDataFileView.SearchPlaceholder")}
                upDirectoryTitle={t("ImportDataFileView.GoUpDirectory")}
                onUpDirectory={goUpDirectory}
                onBreadcrumbClick={handleBreadcrumbClick}
                onSearchChange={setSearchValue}
              />
            </div>

            <div className="flex-1 min-h-0">
              <FileListTable
                files={sortedFiles}
                onFileClick={handleFileClick}
                fileNameHeader={t("ImportDataFileView.FileNameHeader")}
                sizeHeader={t("ImportDataFileView.SizeHeader")}
                lastModifiedHeader={t("ImportDataFileView.LastModifiedHeader")}
                maxHeight="100%"
                className="h-full"
                sortField={sortField}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
            </div>

            <div className="bg-white dark:bg-gray-800/50 p-3 rounded-lg border border-border-color dark:border-gray-700 shrink-0">
              <h2 className="text-main dark:text-white text-base font-bold mb-2">
                {t("SaveDataView.FileSettings")}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <FormField
                  label={t("SaveDataView.DataName")}
                  htmlFor="table-name"
                >
                  <Select
                    id="table-name"
                    value={selectedTableName}
                    onValueChange={(value) => {
                      setSelectedTableName(value);
                      setFileName(value);
                    }}
                  >
                    {tableNameList.map((tableName) => (
                      <SelectItem key={tableName} value={tableName}>
                        {tableName}
                      </SelectItem>
                    ))}
                  </Select>
                </FormField>

                <FormField
                  label={t("SaveDataView.FileName")}
                  htmlFor="file-name"
                >
                  <InputText
                    id="file-name"
                    value={fileName}
                    change={(e) => setFileName(e.target.value)}
                    placeholder={t("SaveDataView.FileNamePlaceholder")}
                    error={errorMessage.fileName}
                  />
                </FormField>

                <FormField
                  label={t("SaveDataView.FileFormat")}
                  htmlFor="file-format"
                >
                  <Select
                    id="file-format"
                    value={fileFormat}
                    onValueChange={(value) =>
                      setFileFormat(value as FileFormat)
                    }
                  >
                    {fileFormatOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </Select>
                </FormField>
              </div>
            </div>
          </div>
          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={t("SaveDataView.Save")}
            onCancel={handleCancel}
            onSelect={handleSave}
          />
        </>
      )}
    </PageLayout>
  );
};
