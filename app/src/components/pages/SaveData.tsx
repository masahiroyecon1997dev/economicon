import { useForm, useStore } from "@tanstack/react-form";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  checkFileExists,
  getFiles,
  getFilesSafe,
} from "@/api/bridge/tauri-commands";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { ExportFileBody } from "@/api/zod/data/data";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { useCurrentPageStore } from "@/stores/currentView";
import { useFilesStore } from "@/stores/files";
import { useLoadingStore } from "@/stores/loading";
import { useSettingsStore } from "@/stores/settings";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type {
  FileType,
  SortDirection,
  SortField,
} from "@/types/commonTypes";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { CancelButtonBar } from "@/components/molecules/ActionBar/CancelButtonBar";
import { FormField } from "@/components/molecules/Form/FormField";
import { NavigationSearchBar } from "@/components/molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "@/components/molecules/Table/FileListTable";
import { PageLayout } from "@/components/templates/PageLayout";

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

  const [searchValue, setSearchValue] = useState("");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const form = useForm({
    defaultValues: {
      tableName: activeTableName || "",
      fileName: activeTableName || "",
      format: "csv" as FileFormat,
    },
    validators: {
      onSubmit: ExportFileBody.pick({
        tableName: true,
        fileName: true,
        format: true,
      }),
    },
    onSubmit: async ({ value }) => {
      const fullFileName = value.fileName.endsWith(
        getFileExtension(value.format),
      )
        ? value.fileName
        : value.fileName + getFileExtension(value.format);

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
        const response = await getEconomiconAppAPI().exportFile({
          tableName: value.tableName,
          directoryPath,
          fileName: value.fileName,
          format: value.format,
          separator: value.format === "csv" ? "," : undefined,
          sheetName: value.format === "excel" ? "Sheet1" : undefined,
        });

        if (response.code === "OK") {
          await showMessageDialog(
            t("Common.OK"),
            t("SaveDataView.SaveSuccess", { path: response.result.filePath }),
          );
          setCurrentView("DataPreview");
        } else {
          await showMessageDialog(
            t("Error.Error"),
            getResponseErrorMessage(response, t("Error.UnexpectedError")),
          );
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          extractApiErrorMessage(error, t("Error.UnexpectedError")),
        );
      } finally {
        clearLoading();
      }
    },
  });

  const isSubmitting = useStore(form.store, (state) => state.isSubmitting);

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
      form.setFieldValue("fileName", baseName);
      // 拡張子がサポートファーマットなら fileFormat も連動
      if (ext === "csv") form.setFieldValue("format", "csv");
      else if (ext === "xlsx" || ext === "xls")
        form.setFieldValue("format", "excel");
      else if (ext === "parquet") form.setFieldValue("format", "parquet");
    }
  };

  const getFileExtension = (fileFormat: FileFormat): string => {
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
        <div className="flex flex-col justify-end h-full gap-4">
          <CancelButtonBar
            cancelText={t("Common.Cancel")}
            onCancel={hadleCancelNoTables}
          />
        </div>
      ) : (
        <>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              void form.handleSubmit();
            }}
            className="flex flex-col gap-3 flex-1 min-h-0"
          >
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
                <form.Field name="tableName">
                  {(field) => (
                    <FormField
                      label={t("SaveDataView.DataName")}
                      htmlFor="table-name"
                      error={extractFieldError(field.state.meta.errors)}
                    >
                      <Select
                        id="table-name"
                        value={field.state.value}
                        onValueChange={(value) => {
                          field.handleChange(value);
                          form.setFieldValue("fileName", value);
                        }}
                        error={extractFieldError(field.state.meta.errors)}
                        disabled={isSubmitting}
                      >
                        {tableNameList.map((tableName) => (
                          <SelectItem key={tableName} value={tableName}>
                            {tableName}
                          </SelectItem>
                        ))}
                      </Select>
                    </FormField>
                  )}
                </form.Field>

                <form.Field name="fileName">
                  {(field) => (
                    <FormField
                      label={t("SaveDataView.FileName")}
                      htmlFor="file-name"
                      error={extractFieldError(field.state.meta.errors)}
                    >
                      <InputText
                        id="file-name"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onBlur={field.handleBlur}
                        placeholder={t("SaveDataView.FileNamePlaceholder")}
                        error={extractFieldError(field.state.meta.errors)}
                        disabled={isSubmitting}
                      />
                    </FormField>
                  )}
                </form.Field>

                <form.Field name="format">
                  {(field) => (
                    <FormField
                      label={t("SaveDataView.FileFormat")}
                      htmlFor="file-format"
                    >
                      <Select
                        id="file-format"
                        value={field.state.value}
                        onValueChange={(value) =>
                          field.handleChange(value as FileFormat)
                        }
                        disabled={isSubmitting}
                      >
                        {fileFormatOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </Select>
                    </FormField>
                  )}
                </form.Field>
              </div>
            </div>
          </form>
          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={t("SaveDataView.Save")}
            onCancel={handleCancel}
            onSelect={() => void form.handleSubmit()}
            isLoading={isSubmitting}
          />
        </>
      )}
    </PageLayout>
  );
};
