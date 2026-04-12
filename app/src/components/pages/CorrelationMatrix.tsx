import { getEconomiconAppAPI } from "@/api/endpoints";
import { CorrelationMethod, MissingHandlingMethod } from "@/api/model";
import { CreateCorrelationTableBody } from "@/api/zod/statistics/statistics";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { CheckboxTagGroup } from "@/components/molecules/Field/CheckboxTagGroup";
import { SelectAllBar } from "@/components/molecules/Field/SelectAllBar";
import { FormField } from "@/components/molecules/Form/FormField";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import { extractApiErrorMessage } from "@/lib/utils/apiError";
import { createFieldError } from "@/lib/utils/formHelpers";
import { cn } from "@/lib/utils/helpers";
import { getTableInfo } from "@/lib/utils/internal";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useForm, useStore } from "@tanstack/react-form";
import { ChevronDown } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export const CorrelationMatrix = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const initialTableName = useTableInfosStore((s) => s.activeTableName) ?? "";
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const [optionsOpen, setOptionsOpen] = useState(false);

  // Column loader (numeric only)
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: true,
      autoLoadOnMount: true,
    });

  const form = useForm({
    defaultValues: {
      tableName: initialTableName,
      columnNames: columnList.map((column) => column.name),
      newTableName: "",
      method: CorrelationMethod.pearson as CorrelationMethod,
      decimalPlaces: 3,
      lowerTriangleOnly: false,
      missingHandling: MissingHandlingMethod.pairwise as MissingHandlingMethod,
    },
    validators: {
      onSubmit: CreateCorrelationTableBody.required(),
    },
    onSubmit: async ({ value }) => {
      try {
        const api = getEconomiconAppAPI();
        const orderedCols = columnList
          .map((c) => c.name)
          .filter((n) => value.columnNames.includes(n));
        const resp = await api.createCorrelationTable({
          tableName: value.tableName,
          columnNames: orderedCols,
          newTableName: value.newTableName.trim(),
          method: value.method,
          decimalPlaces: value.decimalPlaces,
          lowerTriangleOnly: value.lowerTriangleOnly,
          missingHandling: value.missingHandling,
        });
        if (resp.code === "OK") {
          const tableInfo = await getTableInfo(resp.result.tableName);
          addTableInfo(tableInfo);
          setCurrentView("DataPreview");
        } else {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          extractApiErrorMessage(error, t("Error.UnexpectedError")),
        );
      }
    },
  });

  useEffect(() => {
    form.setFieldValue(
      "columnNames",
      columnList.map((column) => column.name),
    );
  }, [columnList, form]);

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  /** Zod の汎用メッセージをフィールド固有の i18n キーで上書きする（Case C）*/
  const tErr = createFieldError(t);

  // Reset columns when table changes
  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    form.setFieldValue("tableName", value);
    form.setFieldValue("columnNames", []);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <PageLayout
      title={t("CorrelationMatrix.Title")}
      description={t("CorrelationMatrix.Description")}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex min-h-0 flex-1 flex-col gap-3"
      >
        {/* ── TOP: テーブル選択（1行コンパクト）── */}
        <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:bg-gray-800 dark:border-gray-700">
          <form.Field name="tableName">
            {(field) => (
              <div className="flex items-center gap-3">
                <label className="shrink-0 text-xs font-medium text-brand-text-main">
                  {t("CorrelationMatrix.DataLabel")}
                </label>
                <div className="flex-1">
                  <Select
                    value={field.state.value}
                    onValueChange={handleTableSelect}
                    disabled={isSubmitting}
                    placeholder={t("CorrelationMatrix.SelectData")}
                    error={tErr(
                      field.state.meta.errors,
                      "CorrelationMatrix.ErrorDataRequired",
                    )}
                  >
                    {tableList.map((name) => (
                      <SelectItem key={name} value={name}>
                        {name}
                      </SelectItem>
                    ))}
                  </Select>
                </div>
                {tErr(
                  field.state.meta.errors,
                  "CorrelationMatrix.ErrorDataRequired",
                ) && (
                  <p className="shrink-0 text-xs text-red-600">
                    {tErr(
                      field.state.meta.errors,
                      "CorrelationMatrix.ErrorDataRequired",
                    )}
                  </p>
                )}
              </div>
            )}
          </form.Field>
        </div>

        {/* ── MIDDLE: 2ペイン（列選択 + オプション）── */}
        <div className="flex min-h-0 flex-1 gap-3">
          {/* 左: 対象列（主役・flex-1）*/}
          <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:bg-gray-800 dark:border-gray-700">
            <div className="mb-2 flex shrink-0 items-center justify-between">
              <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                {t("CorrelationMatrix.ColumnsLabel")}
              </h2>
              {columnList.length > 0 && (
                <SelectAllBar
                  selectAllLabel={t("CorrelationMatrix.SelectAll")}
                  deselectAllLabel={t("CorrelationMatrix.DeselectAll")}
                  onSelectAll={() =>
                    form.setFieldValue(
                      "columnNames",
                      columnList.map((c) => c.name),
                    )
                  }
                  onDeselectAll={() => form.setFieldValue("columnNames", [])}
                  disabled={isSubmitting}
                />
              )}
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto">
              {!selectedTableName ? (
                <p className="text-sm text-brand-text-sub">
                  {t("CorrelationMatrix.SelectData")}
                </p>
              ) : columnList.length === 0 ? (
                <p className="text-sm text-brand-text-sub">
                  {t("CorrelationMatrix.NoColumns")}
                </p>
              ) : (
                <form.Field name="columnNames">
                  {(field) => (
                    <CheckboxTagGroup
                      items={columnList.map((c) => ({
                        value: c.name,
                        label: c.name,
                      }))}
                      checked={new Set(field.state.value)}
                      onToggle={(name) => {
                        const current = new Set(field.state.value);
                        if (current.has(name)) current.delete(name);
                        else current.add(name);
                        field.handleChange([...current]);
                      }}
                      disabled={isSubmitting}
                      error={tErr(
                        field.state.meta.errors,
                        "CorrelationMatrix.ErrorColumnsRequired",
                      )}
                    />
                  )}
                </form.Field>
              )}
            </div>
          </div>

          {/* 右: オプション + 出力名（w-56）*/}
          <div className="flex w-56 shrink-0 flex-col gap-3">
            {/* 出力データ名（常時表示・必須）*/}
            <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm dark:bg-gray-800 dark:border-gray-700">
              <form.Field name="newTableName">
                {(field) => (
                  <FormField
                    label={t("CorrelationMatrix.OutputDataLabel")}
                    htmlFor="new-table-name"
                    error={tErr(
                      field.state.meta.errors,
                      "CorrelationMatrix.ErrorOutputNameRequired",
                    )}
                  >
                    <InputText
                      id="new-table-name"
                      value={field.state.value}
                      onChange={(e) => field.handleChange(e.target.value)}
                      placeholder={t("CorrelationMatrix.OutputDataPlaceholder")}
                      disabled={isSubmitting}
                    />
                  </FormField>
                )}
              </form.Field>
            </div>

            {/* 詳細オプション（accordion）*/}
            <div className="rounded-xl border border-border-color bg-white shadow-sm dark:bg-gray-800 dark:border-gray-700">
              <button
                type="button"
                onClick={() => setOptionsOpen((v) => !v)}
                className="flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors hover:bg-secondary/50 dark:hover:bg-gray-700/50"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-sm font-bold text-text-heading dark:text-gray-100">
                    {t("CorrelationMatrix.AdvancedOptions")}
                  </span>
                  <form.Subscribe selector={(s) => s.values}>
                    {(values) => (
                      <span className="text-xs text-brand-text-main/60 dark:text-gray-400">
                        {t("CorrelationMatrix.AdvancedOptionsSummary", {
                          method: t(
                            `CorrelationMatrix.Method_${values.method}`,
                          ),
                          places: values.decimalPlaces,
                          missing: t(
                            `CorrelationMatrix.Missing_${values.missingHandling}`,
                          ),
                        })}
                      </span>
                    )}
                  </form.Subscribe>
                </div>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 shrink-0 text-brand-text-main/60 transition-transform duration-200",
                    optionsOpen && "rotate-180",
                  )}
                />
              </button>

              {optionsOpen && (
                <div className="border-t border-border-color px-3 pb-4 pt-3 dark:border-gray-700">
                  <div className="flex flex-col gap-3">
                    {/* 計算手法 */}
                    <form.Field name="method">
                      {(field) => (
                        <FormField
                          label={t("CorrelationMatrix.MethodLabel")}
                          htmlFor="correlation-method"
                        >
                          <Select
                            id="correlation-method"
                            value={field.state.value}
                            onValueChange={(v) =>
                              field.handleChange(v as CorrelationMethod)
                            }
                            disabled={isSubmitting}
                          >
                            <SelectItem value={CorrelationMethod.pearson}>
                              {t("CorrelationMatrix.Method_pearson")}
                            </SelectItem>
                            <SelectItem value={CorrelationMethod.spearman}>
                              {t("CorrelationMatrix.Method_spearman")}
                            </SelectItem>
                            <SelectItem value={CorrelationMethod.kendall}>
                              {t("CorrelationMatrix.Method_kendall")}
                            </SelectItem>
                          </Select>
                        </FormField>
                      )}
                    </form.Field>

                    {/* 丸め桁数 */}
                    <form.Field name="decimalPlaces">
                      {(field) => (
                        <FormField
                          label={t("CorrelationMatrix.DecimalPlacesLabel")}
                          htmlFor="decimal-places"
                        >
                          <InputText
                            id="decimal-places"
                            type="number"
                            value={field.state.value.toString()}
                            onChange={(e) => {
                              const v = Math.min(
                                15,
                                Math.max(1, parseInt(e.target.value) || 1),
                              );
                              field.handleChange(v);
                            }}
                            disabled={isSubmitting}
                          />
                        </FormField>
                      )}
                    </form.Field>

                    {/* 下三角のみ */}
                    <form.Field name="lowerTriangleOnly">
                      {(field) => (
                        <FormField
                          label={t("CorrelationMatrix.LowerTriangleOnly")}
                          htmlFor="lower-triangle"
                        >
                          <Select
                            id="lower-triangle"
                            value={field.state.value ? "true" : "false"}
                            onValueChange={(v) =>
                              field.handleChange(v === "true")
                            }
                            disabled={isSubmitting}
                          >
                            <SelectItem value="false">
                              {t("CorrelationMatrix.LowerTriangle_false")}
                            </SelectItem>
                            <SelectItem value="true">
                              {t("CorrelationMatrix.LowerTriangle_true")}
                            </SelectItem>
                          </Select>
                        </FormField>
                      )}
                    </form.Field>

                    {/* 欠損値処理 */}
                    <form.Field name="missingHandling">
                      {(field) => (
                        <FormField
                          label={t("CorrelationMatrix.MissingHandlingLabel")}
                          htmlFor="missing-handling"
                        >
                          <Select
                            id="missing-handling"
                            value={field.state.value}
                            onValueChange={(v) =>
                              field.handleChange(v as MissingHandlingMethod)
                            }
                            disabled={isSubmitting}
                          >
                            <SelectItem value={MissingHandlingMethod.pairwise}>
                              {t("CorrelationMatrix.Missing_pairwise")}
                            </SelectItem>
                            <SelectItem value={MissingHandlingMethod.listwise}>
                              {t("CorrelationMatrix.Missing_listwise")}
                            </SelectItem>
                          </Select>
                        </FormField>
                      )}
                    </form.Field>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── BOTTOM: アクションバー ── */}
        <ActionButtonBar
          cancelText={t("Common.Cancel")}
          selectText={
            isSubmitting
              ? t("CorrelationMatrix.Processing")
              : t("CorrelationMatrix.RunCalculation")
          }
          onCancel={() => setCurrentView("DataPreview")}
          onSelect={() => void form.handleSubmit()}
          disabled={isSubmitting}
          isLoading={isSubmitting}
        />
      </form>
    </PageLayout>
  );
};
