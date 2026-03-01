import * as RadixDialog from "@radix-ui/react-dialog";
import * as RadixSelect from "@radix-ui/react-select";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import { useForm, useStore } from "@tanstack/react-form";
import { Check, ChevronDown, X } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import {
  createImportConfigSchema,
  CSV_ENCODINGS,
  getImportFileType,
  resolveImportSettings,
  type ImportConfigSettings,
} from "../../../lib/utils/importSchema";

type ImportConfigDialogProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  fileInfo: { path: string; name: string } | null;
  onImport: (settings: ImportConfigSettings) => void;
};

export const ImportConfigDialog = ({
  isOpen,
  onOpenChange,
  fileInfo,
  onImport,
}: ImportConfigDialogProps) => {
  const { t } = useTranslation();

  const fileType = fileInfo ? getImportFileType(fileInfo.name) : "other";
  const isCsv = fileType === "csv";
  const isExcel = fileType === "excel";

  const form = useForm({
    defaultValues: {
      tableName: "",
      separatorMode: "comma" as "comma" | "tab" | "other",
      separatorCustom: "",
      encoding: "utf8" as (typeof CSV_ENCODINGS)[number],
      sheetName: "",
    },
    validators: {
      onSubmit: createImportConfigSchema(t),
    },
    onSubmit: ({ value }) => {
      onImport(resolveImportSettings(value, fileType));
      onOpenChange(false);
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  // ダイアログが開くたびに初期値をリセット
  useEffect(() => {
    if (isOpen && fileInfo) {
      const nameWithoutExt = fileInfo.name.replace(/\.[^/.]+$/, "");
      form.reset();
      form.setFieldValue("tableName", nameWithoutExt);
      form.setFieldValue("separatorMode", "comma");
      form.setFieldValue("separatorCustom", "");
      form.setFieldValue("encoding", "utf8");
      form.setFieldValue("sheetName", "");
    }
  }, [isOpen, fileInfo]);

  if (!fileInfo) return null;

  const pillClass = cn(
    "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/50",
    "data-[state=on]:border-brand-primary data-[state=on]:bg-brand-primary data-[state=on]:text-white",
    "data-[state=off]:border-gray-300 data-[state=off]:bg-white data-[state=off]:text-gray-600",
    "data-[state=off]:hover:border-brand-primary/50 data-[state=off]:hover:bg-brand-primary/5",
  );

  const inputClass = cn(
    "flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
    "placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary",
    "disabled:cursor-not-allowed disabled:opacity-50",
  );

  const errorClass = "mt-1 text-xs text-red-500";

  const sectionLabelClass =
    "block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5";

  return (
    <RadixDialog.Root open={isOpen} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <RadixDialog.Content className="fixed left-[50%] top-[50%] z-50 w-full max-w-md translate-x-[-50%] translate-y-[-50%] bg-white p-6 shadow-xl duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 sm:rounded-xl">
          {/* ヘッダー */}
          <div className="mb-5">
            <RadixDialog.Title className="text-base font-semibold text-gray-900">
              {t("ImportDataFileView.ImportDialog.Title")}
            </RadixDialog.Title>
            <RadixDialog.Description className="mt-0.5 truncate text-xs text-gray-400">
              {fileInfo.path}
            </RadixDialog.Description>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              void form.handleSubmit();
            }}
            className="flex flex-col gap-5"
          >
            {/* テーブル名 */}
            <form.Field name="tableName">
              {(field) => (
                <div>
                  <label
                    htmlFor="import-table-name"
                    className="mb-1.5 block text-sm font-medium text-gray-700"
                  >
                    {t("ImportDataFileView.ImportDialog.TableName")}
                    <span className="ml-1 text-red-500">*</span>
                  </label>
                  <input
                    id="import-table-name"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    onBlur={field.handleBlur}
                    placeholder={t(
                      "ImportDataFileView.ImportDialog.TableNamePlaceholder",
                    )}
                    className={cn(
                      inputClass,
                      field.state.meta.errors[0] &&
                        "border-red-400 focus-visible:ring-red-400",
                    )}
                    disabled={isSubmitting}
                  />
                  {field.state.meta.errors[0] && (
                    <p className={errorClass}>
                      {field.state.meta.errors[0].toString()}
                    </p>
                  )}
                </div>
              )}
            </form.Field>

            {/* CSV オプション */}
            {isCsv && (
              <div className="rounded-lg border border-gray-100 bg-gray-50 p-3.5 flex flex-col gap-3.5">
                <span className={sectionLabelClass}>
                  {t("ImportDataFileView.ImportDialog.CsvOptions")}
                </span>

                {/* 区切り文字 */}
                <form.Field name="separatorMode">
                  {(sepModeField) => (
                    <form.Field name="separatorCustom">
                      {(customField) => (
                        <div>
                          <label className="mb-1.5 block text-sm font-medium text-gray-700">
                            {t("ImportDataFileView.ImportDialog.Separator")}
                          </label>
                          <ToggleGroup.Root
                            type="single"
                            value={sepModeField.state.value}
                            onValueChange={(v) => {
                              if (v)
                                sepModeField.handleChange(
                                  v as "comma" | "tab" | "other",
                                );
                            }}
                            className="flex flex-wrap gap-1.5"
                          >
                            <ToggleGroup.Item
                              value="comma"
                              className={pillClass}
                            >
                              {t(
                                "ImportDataFileView.ImportDialog.SeparatorComma",
                              )}
                            </ToggleGroup.Item>
                            <ToggleGroup.Item value="tab" className={pillClass}>
                              {t(
                                "ImportDataFileView.ImportDialog.SeparatorTab",
                              )}
                            </ToggleGroup.Item>
                            <ToggleGroup.Item
                              value="other"
                              className={pillClass}
                            >
                              {t(
                                "ImportDataFileView.ImportDialog.SeparatorOther",
                              )}
                            </ToggleGroup.Item>
                          </ToggleGroup.Root>

                          {/* 「その他」展開入力 */}
                          {sepModeField.state.value === "other" && (
                            <div className="mt-2">
                              <input
                                value={customField.state.value}
                                onChange={(e) =>
                                  customField.handleChange(e.target.value)
                                }
                                onBlur={customField.handleBlur}
                                placeholder={t(
                                  "ImportDataFileView.ImportDialog.SeparatorCustomPlaceholder",
                                )}
                                className={cn(
                                  inputClass,
                                  customField.state.meta.errors[0] &&
                                    "border-red-400 focus-visible:ring-red-400",
                                )}
                                disabled={isSubmitting}
                                maxLength={10}
                              />
                              {customField.state.meta.errors[0] && (
                                <p className={errorClass}>
                                  {customField.state.meta.errors[0].toString()}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </form.Field>
                  )}
                </form.Field>

                {/* エンコーディング */}
                <form.Field name="encoding">
                  {(field) => (
                    <div>
                      <label className="mb-1.5 block text-sm font-medium text-gray-700">
                        {t("ImportDataFileView.ImportDialog.Encoding")}
                      </label>
                      <RadixSelect.Root
                        value={field.state.value}
                        onValueChange={(v) =>
                          field.handleChange(
                            v as (typeof CSV_ENCODINGS)[number],
                          )
                        }
                      >
                        <RadixSelect.Trigger
                          className={cn(
                            inputClass,
                            "flex items-center justify-between",
                          )}
                          aria-label={t(
                            "ImportDataFileView.ImportDialog.Encoding",
                          )}
                        >
                          <RadixSelect.Value />
                          <RadixSelect.Icon>
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          </RadixSelect.Icon>
                        </RadixSelect.Trigger>
                        <RadixSelect.Portal>
                          <RadixSelect.Content
                            className="z-50 overflow-hidden rounded-md border border-gray-200 bg-white shadow-md"
                            position="popper"
                            sideOffset={4}
                          >
                            <RadixSelect.Viewport className="p-1">
                              {CSV_ENCODINGS.map((enc) => (
                                <RadixSelect.Item
                                  key={enc}
                                  value={enc}
                                  className="relative flex cursor-pointer select-none items-center rounded-sm px-8 py-1.5 text-sm outline-none focus:bg-gray-100 data-disabled:pointer-events-none data-disabled:opacity-50"
                                >
                                  <RadixSelect.ItemIndicator className="absolute left-2 flex items-center">
                                    <Check className="h-3.5 w-3.5 text-brand-primary" />
                                  </RadixSelect.ItemIndicator>
                                  <RadixSelect.ItemText>
                                    {enc}
                                  </RadixSelect.ItemText>
                                </RadixSelect.Item>
                              ))}
                            </RadixSelect.Viewport>
                          </RadixSelect.Content>
                        </RadixSelect.Portal>
                      </RadixSelect.Root>
                    </div>
                  )}
                </form.Field>
              </div>
            )}

            {/* Excel オプション */}
            {isExcel && (
              <div className="rounded-lg border border-gray-100 bg-gray-50 p-3.5">
                <span className={sectionLabelClass}>
                  {t("ImportDataFileView.ImportDialog.ExcelOptions")}
                </span>
                <form.Field name="sheetName">
                  {(field) => (
                    <div>
                      <label
                        htmlFor="import-sheet-name"
                        className="mb-1.5 block text-sm font-medium text-gray-700"
                      >
                        {t("ImportDataFileView.ImportDialog.SheetName")}
                      </label>
                      <input
                        id="import-sheet-name"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        onBlur={field.handleBlur}
                        placeholder={t(
                          "ImportDataFileView.ImportDialog.SheetNamePlaceholder",
                        )}
                        className={cn(
                          inputClass,
                          field.state.meta.errors[0] &&
                            "border-red-400 focus-visible:ring-red-400",
                        )}
                        disabled={isSubmitting}
                        maxLength={31}
                      />
                      {field.state.meta.errors[0] && (
                        <p className={errorClass}>
                          {field.state.meta.errors[0].toString()}
                        </p>
                      )}
                    </div>
                  )}
                </form.Field>
              </div>
            )}

            {/* フッターボタン */}
            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={() => onOpenChange(false)}
                className="inline-flex h-9 items-center justify-center rounded-md border border-gray-200 bg-white px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50"
                disabled={isSubmitting}
              >
                {t("Common.Cancel")}
              </button>
              <button
                type="submit"
                className="inline-flex h-9 items-center justify-center rounded-md bg-brand-primary px-4 text-sm font-medium text-white shadow hover:bg-brand-primary-light focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary disabled:pointer-events-none disabled:opacity-50"
                disabled={isSubmitting}
              >
                {t("ImportDataFileView.ImportDialog.Import")}
              </button>
            </div>
          </form>

          <RadixDialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:pointer-events-none"
              aria-label={t("Common.Cancel")}
            >
              <X className="h-4 w-4" />
            </button>
          </RadixDialog.Close>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};

export const ImportConfigDialog = ({
  isOpen,
  onOpenChange,
  fileInfo,
  onImport,
}: ImportConfigDialogProps) => {
  const { t } = useTranslation();
  const [tableName, setTableName] = useState("");
  const [sheetName, setSheetName] = useState("");
  const [separator, setSeparator] = useState(",");

  useEffect(() => {
    if (isOpen && fileInfo) {
      // 初期値設定
      // 拡張子を除いたファイル名をテーブル名とする
      const nameWithoutExt = fileInfo.name.replace(/\.[^/.]+$/, "");
      setTableName(nameWithoutExt);
      setSheetName("");
      setSeparator(",");
    }
  }, [isOpen, fileInfo]);

  const handleImport = () => {
    onImport({
      tableName,
      sheetName: sheetName || undefined,
      separator: separator || undefined,
    });
    onOpenChange(false);
  };

  if (!fileInfo) return null;

  const isExcel =
    fileInfo.name.toLowerCase().endsWith(".xlsx") ||
    fileInfo.name.toLowerCase().endsWith(".xls");
  const isCsv = fileInfo.name.toLowerCase().endsWith(".csv");

  return (
    <RadixDialog.Root open={isOpen} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <RadixDialog.Content className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-white p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg md:w-full">
          <div className="flex flex-col space-y-1.5 text-center sm:text-left">
            <RadixDialog.Title className="text-lg font-semibold leading-none tracking-tight">
              {t("ImportDataFileView.ImportDialog.Title")}
            </RadixDialog.Title>
            <RadixDialog.Description className="text-sm text-gray-500">
              {fileInfo.path}
            </RadixDialog.Description>
          </div>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <label
                htmlFor="tableName"
                className="text-right text-sm font-medium"
              >
                {t("ImportDataFileView.ImportDialog.TableName")}
              </label>
              <input
                id="tableName"
                value={tableName}
                onChange={(e) => setTableName(e.target.value)}
                className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            {isExcel && (
              <div className="grid grid-cols-4 items-center gap-4">
                <label
                  htmlFor="sheetName"
                  className="text-right text-sm font-medium"
                >
                  {t("ImportDataFileView.ImportDialog.SheetName")}
                </label>
                <input
                  id="sheetName"
                  value={sheetName}
                  onChange={(e) => setSheetName(e.target.value)}
                  placeholder="Sheet1"
                  className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            )}

            {isCsv && (
              <div className="grid grid-cols-4 items-center gap-4">
                <label
                  htmlFor="separator"
                  className="text-right text-sm font-medium"
                >
                  {t("ImportDataFileView.ImportDialog.Separator")}
                </label>
                <input
                  id="separator"
                  value={separator}
                  onChange={(e) => setSeparator(e.target.value)}
                  className="col-span-3 flex h-9 w-full rounded-md border border-gray-300 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            )}
          </div>

          <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2">
            <button
              className="mt-2 inline-flex h-9 items-center justify-center rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-900 shadow-sm hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50 sm:mt-0"
              onClick={() => onOpenChange(false)}
            >
              {t("Common.Cancel")}
            </button>
            <button
              className="inline-flex h-9 items-center justify-center rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-gray-50 shadow hover:bg-gray-900/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50"
              onClick={handleImport}
            >
              {t("ImportDataFileView.ImportDialog.Import")}
            </button>
          </div>

          <RadixDialog.Close asChild>
            <button className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-gray-100 data-[state=open]:text-gray-500">
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </button>
          </RadixDialog.Close>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};
