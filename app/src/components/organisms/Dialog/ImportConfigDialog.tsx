import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { cn } from "@/lib/utils/helpers";
import {
  CSV_ENCODINGS,
  createImportConfigSchema,
  getImportFileType,
  resolveImportSettings,
  validateSeparatorCustom,
  validateSheetName,
  type ImportConfigSettings,
} from "@/lib/utils/importSchema";
import * as RadixSelect from "@radix-ui/react-select";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import { useForm, useStore } from "@tanstack/react-form";
import { Check, ChevronDown } from "lucide-react";
import { useTranslation } from "react-i18next";

type ImportConfigDialogProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  fileInfo: { path: string; name: string } | null;
  onImport: (settings: ImportConfigSettings) => void;
};

type ImportConfigDialogContentProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  fileInfo: { path: string; name: string };
  onImport: (settings: ImportConfigSettings) => void;
};

const ImportConfigDialogContent = ({
  isOpen,
  onOpenChange,
  fileInfo,
  onImport,
}: ImportConfigDialogContentProps) => {
  const { t } = useTranslation();

  const fileType = getImportFileType(fileInfo.name);
  const isCsv = fileType === "csv";
  const isExcel = fileType === "excel";

  const importSchema = createImportConfigSchema(t);
  const defaultTableName = fileInfo.name.replace(/\.[^/.]+$/, "");

  const form = useForm({
    defaultValues: {
      tableName: defaultTableName,
      separatorMode: "comma" as "comma" | "tab" | "other",
      separatorCustom: "",
      encoding: "utf8" as (typeof CSV_ENCODINGS)[number],
      sheetName: "",
    },
    onSubmit: ({ value }) => {
      onImport(resolveImportSettings(value, fileType));
      onOpenChange(false);
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  const pillClass = cn(
    "rounded-full border px-3 py-0.5 text-xs font-medium transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary/50",
    "data-[state=on]:border-brand-primary data-[state=on]:bg-brand-primary data-[state=on]:text-white",
    "data-[state=off]:border-gray-300 data-[state=off]:bg-white data-[state=off]:text-gray-600",
    "data-[state=off]:hover:border-brand-primary/50 data-[state=off]:hover:bg-brand-primary/5",
  );

  const inputClass = cn(
    "flex h-9 w-full rounded-md border border-gray-300 dark:border-gray-600 bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
    "placeholder:text-gray-400 dark:placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-primary",
    "disabled:cursor-not-allowed disabled:opacity-50",
  );

  const errorClass = "mt-1 text-xs text-red-500";

  const sectionLabelClass =
    "block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1.5";

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={onOpenChange}
      title={t("ImportDataFileView.ImportDialog.Title")}
      subtitle={fileInfo.path}
      footerVariant="confirm"
      submitLabel={t("ImportDataFileView.ImportDialog.Import")}
      submitFormId="import-form"
      isSubmitting={isSubmitting}
    >
      <form
        id="import-form"
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex flex-col gap-5"
      >
        {/* テーブル名 */}
        <form.Field
          name="tableName"
          validators={{
            onChange: importSchema.shape.tableName,
            onSubmit: importSchema.shape.tableName,
          }}
        >
          {(field) => (
            <div>
              <label
                htmlFor="import-table-name"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                {t("ImportDataFileView.ImportDialog.DataName")}
                <span className="ml-1 text-red-500">*</span>
              </label>
              <input
                id="import-table-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t(
                  "ImportDataFileView.ImportDialog.DataNamePlaceholder",
                )}
                className={cn(
                  inputClass,
                  field.state.meta.errors[0] &&
                    "border-red-400 focus-visible:ring-red-400",
                )}
                disabled={isSubmitting}
              />
              {extractFieldError(field.state.meta.errors) && (
                <p className={errorClass}>
                  {extractFieldError(field.state.meta.errors)}
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
                    <ToggleGroup.Item value="comma" className={pillClass}>
                      {t("ImportDataFileView.ImportDialog.SeparatorComma")}
                    </ToggleGroup.Item>
                    <ToggleGroup.Item value="tab" className={pillClass}>
                      {t("ImportDataFileView.ImportDialog.SeparatorTab")}
                    </ToggleGroup.Item>
                    <ToggleGroup.Item value="other" className={pillClass}>
                      {t("ImportDataFileView.ImportDialog.SeparatorOther")}
                    </ToggleGroup.Item>
                  </ToggleGroup.Root>
                </div>
              )}
            </form.Field>
            <form.Subscribe selector={(s) => s.values.separatorMode}>
              {(separatorMode) => (
                <form.Field
                  name="separatorCustom"
                  validators={{
                    onChange: ({ value }) =>
                      validateSeparatorCustom(value, separatorMode, t),
                    onSubmit: ({ value }) =>
                      validateSeparatorCustom(value, separatorMode, t),
                  }}
                >
                  {(customField) =>
                    separatorMode === "other" ? (
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
                        {extractFieldError(customField.state.meta.errors) && (
                          <p className={errorClass}>
                            {extractFieldError(customField.state.meta.errors)}
                          </p>
                        )}
                      </div>
                    ) : null
                  }
                </form.Field>
              )}
            </form.Subscribe>

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
                      field.handleChange(v as (typeof CSV_ENCODINGS)[number])
                    }
                  >
                    <RadixSelect.Trigger
                      className={cn(
                        inputClass,
                        "flex items-center justify-between",
                      )}
                      aria-label={t("ImportDataFileView.ImportDialog.Encoding")}
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
                              <RadixSelect.ItemText>{enc}</RadixSelect.ItemText>
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
            <form.Field
              name="sheetName"
              validators={{
                onChange: ({ value }) => validateSheetName(value, t),
                onSubmit: ({ value }) => validateSheetName(value, t),
              }}
            >
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
                  {extractFieldError(field.state.meta.errors) && (
                    <p className={errorClass}>
                      {extractFieldError(field.state.meta.errors)}
                    </p>
                  )}
                </div>
              )}
            </form.Field>
          </div>
        )}
      </form>
    </BaseDialog>
  );
};

export const ImportConfigDialog = ({
  isOpen,
  onOpenChange,
  fileInfo,
  onImport,
}: ImportConfigDialogProps) => {
  if (!fileInfo) return null;

  return (
    <ImportConfigDialogContent
      key={`${fileInfo.path}:${isOpen ? "open" : "closed"}`}
      isOpen={isOpen}
      onOpenChange={onOpenChange}
      fileInfo={fileInfo}
      onImport={onImport}
    />
  );
};
