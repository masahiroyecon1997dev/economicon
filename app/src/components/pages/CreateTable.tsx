/**
 * テーブル作成ページ
 *
 * - テーブル名 / 行数を TanStack Form で管理（行数はファイル添付時に任意）
 * - ファイル添付: D&D + ファイルブラウザ + 読み込み設定（任意）
 * - 列リストはローカル state で管理（で並べ替え、 で削除）
 * - 列定義部分のみスクロール。アクションバーは常に最下部に固定
 * - API 成功後はテーブルを即時アクティブ化して DataPreview に遷移
 */
import * as RadixTabs from "@radix-ui/react-tabs";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import { useForm, useStore } from "@tanstack/react-form";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { ArrowDown, ArrowUp, File, Plus, UploadCloud, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import {
  getFiles,
  getFilesSafe,
  TauriFileError,
} from "../../api/bridge/tauri-commands";
import { getEconomiconAPI } from "../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../lib/utils/apiError";
import { cn } from "../../lib/utils/helpers";
import {
  CSV_ENCODINGS,
  getImportFileType,
  type CsvEncoding,
  type SeparatorMode,
} from "../../lib/utils/importSchema";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useFilesStore } from "../../stores/files";
import { useSettingsStore } from "../../stores/settings";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import type {
  FileType,
  SortDirection,
  SortField,
} from "../../types/commonTypes";
import { Button } from "../atoms/Button/Button";
import { InputText } from "../atoms/Input/InputText";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { ErrorAlert } from "../molecules/Alert/ErrorAlert";
import { FormField } from "../molecules/Form/FormField";
import { NavigationSearchBar } from "../molecules/Navigation/NavigationSearchBar";
import { FileListTable } from "../molecules/Table/FileListTable";
import { PageLayout } from "../templates/PageLayout";

const SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".parquet"];

type ColumnEntry = { id: string; name: string };

type FileSettings = {
  hasHeader: boolean;
  separatorMode: SeparatorMode;
  separatorCustom: string;
  csvEncoding: CsvEncoding;
  excelSheetName: string;
};

const DEFAULT_FILE_SETTINGS: FileSettings = {
  hasHeader: true,
  separatorMode: "comma",
  separatorCustom: "",
  csvEncoding: "utf8",
  excelSheetName: "",
};

let _nextId = 1;
const nextId = () => String(_nextId++);

export const CreateTable = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const addTableName = useTableListStore((s) => s.addTableName);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);

  // ファイルブラウザ用ストア
  const files = useFilesStore((s) => s.files);
  const directoryPath = useFilesStore((s) => s.directoryPath);
  const setFiles = useFilesStore((s) => s.setFiles);
  const osName = useSettingsStore((s) => s.osName);
  const pathSeparator = useSettingsStore((s) => s.pathSeparator);

  // 列管理
  const [columns, setColumns] = useState<ColumnEntry[]>([]);
  const [newColName, setNewColName] = useState("");
  const [colError, setColError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // ファイル添付
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string>("");
  const [isDragActive, setIsDragActive] = useState(false);
  const [fileSettings, setFileSettings] = useState<FileSettings>(
    DEFAULT_FILE_SETTINGS,
  );
  const [fileSearchValue, setFileSearchValue] = useState("");
  const [fileSortField, setFileSortField] = useState<SortField | null>(null);
  const [fileSortDirection, setFileSortDirection] =
    useState<SortDirection>(null);

  const newColRef = useRef<HTMLInputElement>(null);

  const handleSelectFile = (path: string, name: string) => {
    setSelectedFilePath(path);
    setSelectedFileName(name);
    setFileSettings(DEFAULT_FILE_SETTINGS);
  };

  // ファイルブラウザを初期ロード
  useEffect(() => {
    if (files.length === 0 && !directoryPath) {
      getFilesSafe("")
        .then((result) => setFiles(result))
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // D&D イベント (Tauri 2)
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
            if (SUPPORTED_EXTENSIONS.includes(ext)) {
              handleSelectFile(filePath, fileName);
            }
          }
        }
      })
      .then((ul) => {
        cleanup = ul;
      });
    return () => cleanup?.();
  }, []);

  // ファイルブラウザ ヘルパー
  const getPathSegments = useCallback(() => {
    if (!directoryPath) return [];
    return directoryPath
      .split(pathSeparator)
      .filter((segment) => segment.length > 0);
  }, [directoryPath, pathSeparator]);

  const buildPathUpToIndex = useCallback(
    (index: number) => {
      const segments = getPathSegments();
      if (index < 0) return pathSeparator;
      const selectedSegments = segments.slice(0, index + 1);
      const basePath = selectedSegments.join(pathSeparator);
      return osName === "Windows" ? basePath + pathSeparator : "/" + basePath;
    },
    [getPathSegments, osName, pathSeparator],
  );

  const changeDirectory = async (newPath: string) => {
    try {
      const result = await getFiles(newPath);
      setFiles(result);
    } catch (e) {
      if (e instanceof TauriFileError && e.errorType === "PathNotFound") {
        try {
          const refreshed = directoryPath
            ? await getFiles(directoryPath)
            : await getFilesSafe("");
          setFiles(refreshed);
        } catch {
          /* ignore */
        }
      }
    }
  };

  const goUpDirectory = async () => {
    const segments = getPathSegments();
    if (segments.length > 0) {
      await changeDirectory(buildPathUpToIndex(segments.length - 2));
    }
  };

  const handleBreadcrumbClick = async (index: number) => {
    await changeDirectory(buildPathUpToIndex(index));
  };

  const removeFile = () => {
    setSelectedFilePath(null);
    setSelectedFileName("");
  };

  const handleBrowserFileClick = async (file: FileType) => {
    if (!file.isFile) {
      const newPath =
        directoryPath === pathSeparator
          ? pathSeparator + file.name
          : directoryPath + pathSeparator + file.name;
      await changeDirectory(newPath);
    } else {
      const ext = file.name.toLowerCase().match(/\.[^.]+$/)?.[0] ?? "";
      if (SUPPORTED_EXTENSIONS.includes(ext)) {
        handleSelectFile(directoryPath + pathSeparator + file.name, file.name);
      }
    }
  };

  const handleFileSort = (field: SortField) => {
    if (fileSortField === field) {
      setFileSortDirection(
        fileSortDirection === "asc"
          ? "desc"
          : fileSortDirection === "desc"
            ? null
            : "asc",
      );
      if (fileSortDirection === "desc") setFileSortField(null);
    } else {
      setFileSortField(field);
      setFileSortDirection("asc");
    }
  };

  const filteredBrowserFiles = files
    .filter((f) => f.name.toLowerCase().includes(fileSearchValue.toLowerCase()))
    .sort((a, b) => {
      if (!fileSortField || !fileSortDirection) return 0;
      if (a.isFile !== b.isFile) return a.isFile ? 1 : -1;
      let aVal: string | number = "";
      let bVal: string | number = "";
      if (fileSortField === "name") {
        aVal = a.name.toLowerCase();
        bVal = b.name.toLowerCase();
      } else if (fileSortField === "size") {
        aVal = a.isFile ? (a.size ?? 0) : 0;
        bVal = b.isFile ? (b.size ?? 0) : 0;
      } else if (fileSortField === "modifiedTime") {
        aVal = a.isFile ? new Date(a.modifiedTime).getTime() : 0;
        bVal = b.isFile ? new Date(b.modifiedTime).getTime() : 0;
      }
      if (aVal < bVal) return fileSortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return fileSortDirection === "asc" ? 1 : -1;
      return 0;
    });

  const fileType = selectedFilePath
    ? getImportFileType(selectedFileName)
    : "other";
  const isCsv = fileType === "csv";
  const isExcel = fileType === "excel";

  // 制御文字チェック
  const hasControlChars = (s: string) =>
    s.split("").some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127);

  // 列操作
  const addColumn = () => {
    const trimmed = newColName.trim();
    if (!trimmed) return;
    if (hasControlChars(trimmed)) {
      setColError(t("CreateTableView.ColumnNameInvalidChars"));
      return;
    }
    if (columns.some((c) => c.name === trimmed)) {
      setColError(t("CreateTableView.ColumnNameDuplicate"));
      return;
    }
    setColumns((prev) => [...prev, { id: nextId(), name: trimmed }]);
    setNewColName("");
    setColError(null);
    setTimeout(() => newColRef.current?.focus(), 0);
  };

  const removeColumn = (id: string) =>
    setColumns((prev) => prev.filter((c) => c.id !== id));

  const moveUp = (idx: number) => {
    if (idx === 0) return;
    setColumns((prev) => {
      const next = [...prev];
      [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
      return next;
    });
  };

  const moveDown = (idx: number) => {
    setColumns((prev) => {
      if (idx >= prev.length - 1) return prev;
      const next = [...prev];
      [next[idx], next[idx + 1]] = [next[idx + 1], next[idx]];
      return next;
    });
  };

  // ToggleGroup の pill スタイル（ImportConfigDialog と同じ）
  const pillClass = cn(
    "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/50",
    "data-[state=on]:border-brand-primary data-[state=on]:bg-brand-primary data-[state=on]:text-white",
    "data-[state=off]:border-gray-300 data-[state=off]:bg-white data-[state=off]:text-gray-600",
    "data-[state=off]:hover:border-brand-primary/50 data-[state=off]:hover:bg-brand-primary/5",
  );

  // フォーム（rowCount は string として管理し、サブミット時にパース）
  const form = useForm({
    defaultValues: { tableName: "", rowCount: "1000" },
    validators: {
      onSubmit: z.object({
        tableName: z
          .string()
          .min(1, t("ValidationMessages.TableNameRequired"))
          .max(128, t("ValidationMessages.TableNameTooLong"))
          .refine(
            (v) => !hasControlChars(v),
            t("ValidationMessages.TableNameInvalidChars"),
          ),
        rowCount: z.string(),
      }),
    },
    onSubmit: async ({ value }) => {
      if (columns.length === 0) {
        setColError(t("CreateTableView.ColumnRequired"));
        return;
      }

      const rowCountRaw = value.rowCount.trim();
      const rowCountNum = rowCountRaw ? parseInt(rowCountRaw, 10) : null;
      if (!selectedFilePath) {
        if (rowCountNum === null || isNaN(rowCountNum) || rowCountNum < 1)
          return;
      }

      setColError(null);
      setApiError(null);

      const csvSeparator =
        fileSettings.separatorMode === "comma"
          ? ","
          : fileSettings.separatorMode === "tab"
            ? "\t"
            : fileSettings.separatorCustom || ",";

      try {
        const response = await getEconomiconAPI().createTable({
          tableName: value.tableName,
          rowCount: rowCountNum,
          columnNames: columns.map((c) => c.name),
          filePath: selectedFilePath ?? undefined,
          hasHeader: fileSettings.hasHeader,
          csvSeparator,
          csvEncoding: fileSettings.csvEncoding,
          excelSheetName: fileSettings.excelSheetName || undefined,
        });

        if (response.code === "OK") {
          const info = await getTableInfo(value.tableName);
          addTableName(value.tableName);
          addTableInfo(info);
          setCurrentView("DataPreview");
        } else {
          setApiError(
            getResponseErrorMessage(response, t("Error.UnexpectedError")),
          );
        }
      } catch (error) {
        setApiError(extractApiErrorMessage(error, t("Error.UnexpectedError")));
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  return (
    <PageLayout
      title={t("CreateTableView.Title")}
      description={t("CreateTableView.Description")}
    >
      {/* form: 残り全高さを占有し、アクションバーを常に最下部に固定 */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex-1 flex flex-col min-h-0"
      >
        {/* ============================================================
            コンテンツエリア（アクションバーより上スクロール制御）
        ============================================================ */}
        <div className="flex-1 flex flex-col min-h-0">
          {/*  テーブル基本設定  */}
          <div className="shrink-0 pt-2 pb-4 border-b border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-4">
              {/* テーブル名 */}
              <form.Field
                name="tableName"
                validators={{
                  onChange: ({ value }) => {
                    if (!value.trim())
                      return t("ValidationMessages.TableNameRequired");
                    if (value.length > 128)
                      return t("ValidationMessages.TableNameTooLong");
                    if (hasControlChars(value))
                      return t("ValidationMessages.TableNameInvalidChars");
                    return undefined;
                  },
                }}
              >
                {(field) => {
                  const errorMsg = field.state.meta.isTouched
                    ? (field.state.meta.errors[0] as string | undefined)
                    : undefined;
                  return (
                    <FormField
                      label={t("CreateTableView.TableName")}
                      htmlFor="ct-table-name"
                      error={errorMsg}
                    >
                      <InputText
                        id="ct-table-name"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onBlur={field.handleBlur}
                        placeholder={t("CreateTableView.TableNamePlaceholder")}
                        disabled={isSubmitting}
                        autoFocus
                      />
                    </FormField>
                  );
                }}
              </form.Field>

              {/* 行数 */}
              <form.Field
                name="rowCount"
                validators={{
                  onChange: ({ value }) => {
                    if (selectedFilePath) return undefined;
                    const num = parseInt(value, 10);
                    if (!value.trim() || isNaN(num) || num < 1)
                      return t("ValidationMessages.NumRowsMoreThan0");
                    return undefined;
                  },
                }}
              >
                {(field) => {
                  const errorMsg = field.state.meta.isTouched
                    ? (field.state.meta.errors[0] as string | undefined)
                    : undefined;
                  return (
                    <FormField
                      label={t("CreateTableView.RowCount")}
                      htmlFor="ct-row-count"
                      error={errorMsg}
                    >
                      <InputText
                        id="ct-row-count"
                        type="number"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onBlur={field.handleBlur}
                        placeholder={
                          selectedFilePath
                            ? t("CreateTableView.RowCountOptional")
                            : ""
                        }
                        disabled={isSubmitting}
                      />
                      {selectedFilePath && (
                        <p className="mt-1 text-xs text-gray-400">
                          {t("CreateTableView.RowCountOptional")}
                        </p>
                      )}
                    </FormField>
                  );
                }}
              </form.Field>
            </div>
          </div>

          {/* ── ファイル添付（任意）──────────────────────────────── */}
          <div className="shrink-0 py-4 border-b border-gray-200 dark:border-gray-700 flex flex-col gap-2">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {t("CreateTableView.FileSection")}
            </h2>

            {/* ファイル未選択  D&D / ファイル選択タブ */}
            {!selectedFilePath && (
              <RadixTabs.Root defaultValue="dragDrop" className="flex flex-col">
                <RadixTabs.List className="flex w-full border-b border-gray-200 dark:border-gray-700">
                  {(
                    [
                      { value: "dragDrop", key: "DragAndDropTab" },
                      { value: "fileSelect", key: "FileSelectTab" },
                    ] as const
                  ).map(({ value, key }) => (
                    <RadixTabs.Trigger
                      key={value}
                      value={value}
                      className="group relative flex h-8 items-center px-4 text-xs font-medium text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 data-[state=active]:font-semibold data-[state=active]:text-gray-900 dark:data-[state=active]:text-gray-100 focus-visible:outline-none"
                    >
                      {t(`CreateTableView.${key}`)}
                      <div className="absolute -bottom-px left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100 opacity-0 group-data-[state=active]:opacity-100" />
                    </RadixTabs.Trigger>
                  ))}
                </RadixTabs.List>

                {/* D&D タブ */}
                <RadixTabs.Content value="dragDrop" className="outline-none">
                  <div
                    className={cn(
                      "flex h-28 w-full flex-col items-center justify-center rounded-lg border-2 border-dashed transition-colors mt-2",
                      isDragActive
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
                        : "border-gray-300 hover:border-gray-400 bg-gray-50 dark:bg-gray-800/30",
                    )}
                  >
                    <UploadCloud
                      className={cn(
                        "mb-2 h-8 w-8",
                        isDragActive ? "text-blue-500" : "text-gray-400",
                      )}
                    />
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      {isDragActive
                        ? t("CreateTableView.DragDropAreaTitleActive")
                        : t("CreateTableView.DragDropAreaTitle")}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      {t("CreateTableView.DragDropAreaDescription")}
                    </p>
                  </div>
                </RadixTabs.Content>

                {/* ファイル選択タブ */}
                <RadixTabs.Content
                  value="fileSelect"
                  className="flex flex-col gap-1.5 outline-none mt-2 h-48"
                >
                  <NavigationSearchBar
                    pathSegments={getPathSegments()}
                    searchValue={fileSearchValue}
                    searchPlaceholder={t("CreateTableView.SearchPlaceholder")}
                    upDirectoryTitle={t("CreateTableView.GoUpDirectory")}
                    onUpDirectory={goUpDirectory}
                    onBreadcrumbClick={handleBreadcrumbClick}
                    onSearchChange={setFileSearchValue}
                  />
                  <FileListTable
                    files={filteredBrowserFiles}
                    onFileClick={handleBrowserFileClick}
                    fileNameHeader={t("ImportDataFileView.FileNameHeader")}
                    sizeHeader={t("ImportDataFileView.SizeHeader")}
                    lastModifiedHeader={t(
                      "ImportDataFileView.LastModifiedHeader",
                    )}
                    maxHeight="100%"
                    className="flex-1 min-h-0"
                    sortField={fileSortField}
                    sortDirection={fileSortDirection}
                    onSort={handleFileSort}
                  />
                </RadixTabs.Content>
              </RadixTabs.Root>
            )}

            {/* ファイル選択済  チップ + 設定パネル */}
            {selectedFilePath && (
              <div className="flex flex-col gap-3">
                {/* ファイルチップ */}
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                  <File className="h-4 w-4 shrink-0 text-blue-500" />
                  <span className="flex-1 text-xs font-mono text-blue-800 dark:text-blue-300 truncate">
                    {selectedFileName}
                  </span>
                  <button
                    type="button"
                    onClick={removeFile}
                    disabled={isSubmitting}
                    className="shrink-0 text-blue-400 hover:text-red-500 transition-colors focus:outline-none disabled:cursor-not-allowed"
                    aria-label={t("CreateTableView.RemoveFile")}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* 読み込み設定パネル */}
                <div className="flex flex-col gap-3 px-3 py-3 rounded-lg bg-gray-50 dark:bg-gray-800/30 border border-gray-200 dark:border-gray-700">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                    {t("CreateTableView.FileOptions")}
                  </p>

                  {/* ヘッダ行 */}
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={fileSettings.hasHeader}
                      onChange={(e) =>
                        setFileSettings((prev) => ({
                          ...prev,
                          hasHeader: e.target.checked,
                        }))
                      }
                      disabled={isSubmitting}
                      className="h-3.5 w-3.5 rounded border-gray-300 accent-brand-primary"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">
                      {t("CreateTableView.HasHeader")}
                    </span>
                  </label>

                  {/* CSV オプション */}
                  {isCsv && (
                    <>
                      {/* 区切り文字 */}
                      <div className="flex flex-col gap-1.5">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {t("CreateTableView.CsvSeparator")}
                        </p>
                        <ToggleGroup.Root
                          type="single"
                          value={fileSettings.separatorMode}
                          onValueChange={(v) =>
                            v &&
                            setFileSettings((prev) => ({
                              ...prev,
                              separatorMode: v as SeparatorMode,
                            }))
                          }
                          className="flex flex-wrap gap-1.5"
                        >
                          {(
                            [
                              ["comma", "SeparatorComma"],
                              ["tab", "SeparatorTab"],
                              ["other", "SeparatorOther"],
                            ] as const
                          ).map(([val, key]) => (
                            <ToggleGroup.Item
                              key={val}
                              value={val}
                              className={pillClass}
                            >
                              {t(`CreateTableView.${key}`)}
                            </ToggleGroup.Item>
                          ))}
                        </ToggleGroup.Root>
                        {fileSettings.separatorMode === "other" && (
                          <InputText
                            value={fileSettings.separatorCustom}
                            onChange={(e) =>
                              setFileSettings((prev) => ({
                                ...prev,
                                separatorCustom: e.target.value,
                              }))
                            }
                            placeholder={t(
                              "CreateTableView.SeparatorCustomPlaceholder",
                            )}
                            disabled={isSubmitting}
                            className="w-44"
                          />
                        )}
                      </div>

                      {/* エンコーディング */}
                      <div className="flex flex-col gap-1.5">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {t("CreateTableView.Encoding")}
                        </p>
                        <ToggleGroup.Root
                          type="single"
                          value={fileSettings.csvEncoding}
                          onValueChange={(v) =>
                            v &&
                            setFileSettings((prev) => ({
                              ...prev,
                              csvEncoding: v as CsvEncoding,
                            }))
                          }
                          className="flex flex-wrap gap-1.5"
                        >
                          {CSV_ENCODINGS.map((enc) => (
                            <ToggleGroup.Item
                              key={enc}
                              value={enc}
                              className={pillClass}
                            >
                              {enc}
                            </ToggleGroup.Item>
                          ))}
                        </ToggleGroup.Root>
                      </div>
                    </>
                  )}

                  {/* Excel オプション */}
                  {isExcel && (
                    <div className="flex flex-col gap-1.5">
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {t("CreateTableView.ExcelSheetName")}
                      </p>
                      <InputText
                        value={fileSettings.excelSheetName}
                        onChange={(e) =>
                          setFileSettings((prev) => ({
                            ...prev,
                            excelSheetName: e.target.value,
                          }))
                        }
                        placeholder={t(
                          "CreateTableView.ExcelSheetNamePlaceholder",
                        )}
                        disabled={isSubmitting}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/*  列定義（ 列リストのみスクロール） */}
          <div className="flex-1 flex flex-col min-h-0 py-4 gap-2">
            {/* セクションヘッダー */}
            <h2 className="shrink-0 text-sm font-semibold text-gray-700 dark:text-gray-300">
              {t("CreateTableView.ColumnsSection")}
              {columns.length > 0 && (
                <span className="ml-2 text-xs font-normal text-gray-400">
                  {t("CreateTableView.ColumnsCount", {
                    count: columns.length,
                  })}
                </span>
              )}
            </h2>

            {/* 列リストコンテナ（ここだけスクロール） */}
            <div
              className={cn(
                "flex-1 min-h-0 overflow-y-auto rounded-lg border",
                columns.length > 0
                  ? "border-gray-200 dark:border-gray-700"
                  : "border-dashed border-gray-200 dark:border-gray-700",
              )}
            >
              {columns.length === 0 ? (
                <div className="flex h-full items-center justify-center p-8">
                  <p className="text-xs text-center text-gray-400">
                    {t("CreateTableView.ColumnsEmpty")}
                  </p>
                </div>
              ) : (
                <ul className="flex flex-col">
                  {columns.map((col, idx) => (
                    <li
                      key={col.id}
                      className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border-b last:border-b-0 border-gray-100 dark:border-gray-700"
                    >
                      {/* 並べ替えボタン */}
                      <div className="flex flex-col gap-0.5 shrink-0">
                        <button
                          type="button"
                          onClick={() => moveUp(idx)}
                          disabled={idx === 0 || isSubmitting}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-25 disabled:cursor-not-allowed focus:outline-none"
                          aria-label={t("CreateTableView.MoveUp")}
                        >
                          <ArrowUp className="size-3" />
                        </button>
                        <button
                          type="button"
                          onClick={() => moveDown(idx)}
                          disabled={idx === columns.length - 1 || isSubmitting}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-25 disabled:cursor-not-allowed focus:outline-none"
                          aria-label={t("CreateTableView.MoveDown")}
                        >
                          <ArrowDown className="size-3" />
                        </button>
                      </div>

                      {/* 連番 */}
                      <span className="text-xs text-gray-400 w-5 text-right shrink-0 tabular-nums">
                        {idx + 1}
                      </span>

                      {/* 列名 */}
                      <span className="flex-1 text-sm font-mono text-gray-800 dark:text-gray-200 truncate">
                        {col.name}
                      </span>

                      {/* 削除ボタン */}
                      <button
                        type="button"
                        onClick={() => removeColumn(col.id)}
                        disabled={isSubmitting}
                        className="shrink-0 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors disabled:cursor-not-allowed focus:outline-none"
                        aria-label={t("CreateTableView.RemoveColumn")}
                      >
                        <X className="size-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* 列追加インプット */}
            <div className="shrink-0 flex gap-2">
              <div className="flex-1">
                <InputText
                  ref={newColRef}
                  value={newColName}
                  onChange={(e) => {
                    setNewColName(e.target.value);
                    if (colError) setColError(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addColumn();
                    }
                  }}
                  placeholder={t("CreateTableView.NewColumnPlaceholder")}
                  disabled={isSubmitting}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                onClick={addColumn}
                disabled={isSubmitting || !newColName.trim()}
                className="shrink-0 gap-1.5"
              >
                <Plus className="size-4" />
                {t("CreateTableView.AddColumn")}
              </Button>
            </div>

            {/* 列エラー */}
            {colError && (
              <p className="shrink-0 text-xs text-red-500 dark:text-red-400">
                {colError}
              </p>
            )}
          </div>
        </div>

        {/* API エラー */}
        {apiError && (
          <div className="shrink-0 pb-2">
            <ErrorAlert message={apiError} />
          </div>
        )}

        {/*  アクションバー（常に最下部に固定） */}
        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={isSubmitting ? "..." : t("CreateTableView.Submit")}
          onCancel={() => setCurrentView("DataPreview")}
          onSelect={() => {}}
          onSelectType="submit"
          disabled={isSubmitting}
        />
      </form>
    </PageLayout>
  );
};
