import { useForm, useStore } from "@tanstack/react-form";
import { ChevronDown, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../api/endpoints";
import type { StandardErrorSettings } from "../../../api/model";
import { MissingValueHandlingType } from "../../../api/model";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { showMessageDialog } from "../../../lib/dialog/message";
import { cn } from "../../../lib/utils/helpers";
import { useRegressionResultsStore } from "../../../stores/regressionResults";
import { useTableListStore } from "../../../stores/tableList";
import type { LinearRegressionResultType } from "../../../types/commonTypes";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { VariableSelectorField } from "../../molecules/Field/VariableSelectorField";
import { FormField } from "../../molecules/Form/FormField";

const createRegressionSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.TableNameSelect")),
    dependentVariable: z
      .string()
      .min(1, t("ValidationMessages.DependentVariableRequired")),
    explanatoryVariables: z
      .array(z.string())
      .min(1, t("ValidationMessages.ExplanatoryVariablesRequired")),
    standardErrorMethod: z.string(),
    hasConst: z.boolean(),
    missingValueHandling: z.string(),
  });

type LinearRegressionFormProps = {
  onCancel: () => void;
  onAnalysisComplete?: (resultIndex: number) => void;
};

export const LinearRegressionForm = ({
  onCancel,
  onAnalysisComplete,
}: LinearRegressionFormProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
    });
  const addResult = useRegressionResultsStore((state) => state.addResult);

  const form = useForm({
    defaultValues: {
      tableName: selectedTableName,
      dependentVariable: "",
      explanatoryVariables: [] as string[],
      standardErrorMethod: "nonrobust",
      hasConst: true,
      missingValueHandling: MissingValueHandlingType.remove as string,
    },
    validators: {
      onSubmit: createRegressionSchema(t),
    },
    onSubmit: async ({ value }) => {
      try {
        const api = getEconomiconAPI();
        const regressionResponse = await api.regression({
          tableName: value.tableName,
          dependentVariable: value.dependentVariable,
          explanatoryVariables: value.explanatoryVariables,
          hasConst: value.hasConst,
          missingValueHandling:
            value.missingValueHandling as MissingValueHandlingType,
          analysis: { method: "ols" },
          standardError: {
            method: value.standardErrorMethod,
          } as StandardErrorSettings,
        });

        if (regressionResponse.code === "OK" && regressionResponse.result) {
          const { resultId } = regressionResponse.result;
          const resultResponse = await api.getAnalysisResult(resultId);
          if (resultResponse.code === "OK" && resultResponse.result) {
            addResult(
              resultResponse.result.result
                .regressionOutput as LinearRegressionResultType,
            );
            const newIndex =
              useRegressionResultsStore.getState().results.length - 1;
            onAnalysisComplete?.(newIndex);
            return;
          }
        }
        await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : t("Error.UnexpectedError");
        await showMessageDialog(t("Error.Error"), errorMessage);
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const [optionsOpen, setOptionsOpen] = useState(false);

  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    form.setFieldValue("tableName", value);
    form.setFieldValue("dependentVariable", "");
    form.setFieldValue("explanatoryVariables", []);
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
      className="flex flex-col gap-4"
    >
      {/* テーブル選択セクション */}
      <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
        <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
          {t("LinearRegressionForm.SelectDataTable")}
        </h2>
        <form.Field name="tableName">
          {(field) => (
            <FormField
              label={t("LinearRegressionForm.DataTable")}
              htmlFor="data-table"
              error={field.state.meta.errors[0]?.toString()}
            >
              <Select
                id="data-table"
                value={field.state.value}
                onValueChange={handleTableSelect}
                disabled={isSubmitting}
                error={field.state.meta.errors[0]?.toString()}
                placeholder={t("LinearRegressionForm.SelectATable")}
              >
                {tableList.map((table, index) => (
                  <SelectItem key={index} value={table}>
                    {table}
                  </SelectItem>
                ))}
              </Select>
            </FormField>
          )}
        </form.Field>
      </div>

      {/* 変数選択セクション */}
      <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
        <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
          {t("LinearRegressionForm.SelectVariables")}
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <form.Field name="dependentVariable">
            {(field) => (
              <VariableSelectorField
                label={t("LinearRegressionForm.DependentVariable")}
                description={t(
                  "LinearRegressionForm.DependentVariableDescription",
                )}
                mode="single"
                columns={columnList}
                selectedValue={field.state.value}
                onSingleChange={(v) => field.handleChange(v)}
                error={field.state.meta.errors[0]?.toString()}
                disabled={isSubmitting}
                name="dependentVariable"
              />
            )}
          </form.Field>
          <form.Field name="explanatoryVariables">
            {(field) => (
              <VariableSelectorField
                label={t("LinearRegressionForm.ExplanatoryVariables")}
                description={t(
                  "LinearRegressionForm.ExplanatoryVariablesDescription",
                )}
                mode="multiple"
                columns={columnList}
                selectedValues={field.state.value}
                onMultipleChange={(v) => field.handleChange(v)}
                error={field.state.meta.errors[0]?.toString()}
                disabled={isSubmitting}
                name="explanatoryVariables"
              />
            )}
          </form.Field>
        </div>

        {/* 選択済み説明変数タグ */}
        <form.Subscribe selector={(s) => s.values.explanatoryVariables}>
          {(explanatoryVariables) => (
            <div className="mt-4">
              <label className="mb-1.5 block text-xs font-medium text-brand-text-main">
                {t("LinearRegressionForm.SelectedExplanatoryVariables")}
              </label>
              <div className="flex min-h-11 flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-2">
                {explanatoryVariables.length === 0 ? (
                  <span className="text-xs text-brand-text-main/60">
                    {t("LinearRegressionForm.NoVariablesSelected")}
                  </span>
                ) : (
                  explanatoryVariables.map((variable, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center gap-1 rounded-md bg-brand-accent px-2 py-1 text-xs text-white"
                    >
                      <span className="max-w-30 truncate">{variable}</span>
                      <button
                        type="button"
                        onClick={() =>
                          form.setFieldValue(
                            "explanatoryVariables",
                            explanatoryVariables.filter((v) => v !== variable),
                          )
                        }
                        className="rounded-full p-0.5 hover:bg-white/20 focus:outline-none focus:ring-1 focus:ring-white"
                        aria-label={`Remove ${variable}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>
          )}
        </form.Subscribe>
      </div>

      {/* 詳細オプション（アコーディオン） */}
      <div className="rounded-xl border border-border-color bg-white shadow-sm">
        <button
          type="button"
          onClick={() => setOptionsOpen((v) => !v)}
          className="flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors hover:bg-secondary/50"
        >
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-bold text-text-heading">
              {t("LinearRegressionForm.AdvancedOptions")}
            </span>
            <form.Subscribe selector={(s) => s.values}>
              {(values) => (
                <span className="text-xs text-brand-text-main/60">
                  {t("LinearRegressionForm.AdvancedOptionsSummary", {
                    se: t(
                      `LinearRegressionForm.StandardError_${values.standardErrorMethod}`,
                    ),
                    const: values.hasConst
                      ? t("LinearRegressionForm.HasConstYes")
                      : t("LinearRegressionForm.HasConstNo"),
                    missing: t(
                      `LinearRegressionForm.MissingValue_${values.missingValueHandling}`,
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
          <div className="border-t border-border-color px-3 pb-4 pt-3">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {/* 標準誤差 */}
              <form.Field name="standardErrorMethod">
                {(field) => (
                  <FormField
                    label={t("LinearRegressionForm.StandardErrorMethod")}
                    htmlFor="standard-error-method"
                  >
                    <Select
                      id="standard-error-method"
                      value={field.state.value}
                      onValueChange={(v) => field.handleChange(v)}
                      disabled={isSubmitting}
                    >
                      <SelectItem value="nonrobust">
                        {t("LinearRegressionForm.StandardError_nonrobust")}
                      </SelectItem>
                      <SelectItem value="robust">
                        {t("LinearRegressionForm.StandardError_robust")}
                      </SelectItem>
                    </Select>
                  </FormField>
                )}
              </form.Field>

              {/* 定数項 */}
              <form.Field name="hasConst">
                {(field) => (
                  <FormField
                    label={t("LinearRegressionForm.HasConst")}
                    htmlFor="has-const"
                  >
                    <Select
                      id="has-const"
                      value={field.state.value ? "true" : "false"}
                      onValueChange={(v) => field.handleChange(v === "true")}
                      disabled={isSubmitting}
                    >
                      <SelectItem value="true">
                        {t("LinearRegressionForm.HasConstYes")}
                      </SelectItem>
                      <SelectItem value="false">
                        {t("LinearRegressionForm.HasConstNo")}
                      </SelectItem>
                    </Select>
                  </FormField>
                )}
              </form.Field>

              {/* 欠損値処理 */}
              <form.Field name="missingValueHandling">
                {(field) => (
                  <FormField
                    label={t("LinearRegressionForm.MissingValueHandling")}
                    htmlFor="missing-value-handling"
                  >
                    <Select
                      id="missing-value-handling"
                      value={field.state.value}
                      onValueChange={(v) =>
                        field.handleChange(v as MissingValueHandlingType)
                      }
                      disabled={isSubmitting}
                    >
                      <SelectItem value={MissingValueHandlingType.remove}>
                        {t("LinearRegressionForm.MissingValue_remove")}
                      </SelectItem>
                      <SelectItem value={MissingValueHandlingType.ignore}>
                        {t("LinearRegressionForm.MissingValue_ignore")}
                      </SelectItem>
                      <SelectItem value={MissingValueHandlingType.error}>
                        {t("LinearRegressionForm.MissingValue_error")}
                      </SelectItem>
                    </Select>
                  </FormField>
                )}
              </form.Field>
            </div>
          </div>
        )}
      </div>

      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isSubmitting
            ? t("LinearRegressionForm.Processing")
            : t("LinearRegressionForm.RunAnalysis")
        }
        onCancel={onCancel}
        onSelect={() => {}}
        onSelectType="submit"
      />
    </form>
  );
};
