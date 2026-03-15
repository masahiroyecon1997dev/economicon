import { useForm, useStore } from "@tanstack/react-form";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../api/endpoints";
import type {
  AnalysisResultDetail,
  StandardErrorSettings,
} from "../../../api/model";
import {
  MissingValueHandlingType,
  RobustStandardErrorHcType,
} from "../../../api/model";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { showMessageDialog } from "../../../lib/dialog/message";
import { cn } from "../../../lib/utils/helpers";
import { useRegressionResultsStore } from "../../../stores/regressionResults";
import { useTableListStore } from "../../../stores/tableList";
import type { LinearRegressionResultType } from "../../../types/commonTypes";
import { InputText } from "../../atoms/Input/InputText";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { VariableSelectorField } from "../../molecules/Field/VariableSelectorField";
import { FormField } from "../../molecules/Form/FormField";

const createRegressionSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.DataNameSelect")),
    dependentVariable: z
      .string()
      .min(1, t("ValidationMessages.DependentVariableRequired")),
    explanatoryVariables: z
      .array(z.string())
      .min(1, t("ValidationMessages.ExplanatoryVariablesRequired")),
    standardErrorMethod: z.string(),
    hacMaxlags: z.number().min(0),
    clusterGroups: z.array(z.string()),
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
      hacMaxlags: 1,
      clusterGroups: [] as string[],
      hasConst: true,
      missingValueHandling: MissingValueHandlingType.remove as string,
    },
    validators: {
      onSubmit: createRegressionSchema(t),
    },
    onSubmit: async ({ value }) => {
      try {
        const api = getEconomiconAPI();
        const seMethod = value.standardErrorMethod;
        let standardError: StandardErrorSettings;
        if (seMethod === "hac") {
          standardError = { method: "hac", maxlags: value.hacMaxlags };
        } else if (seMethod === "cluster") {
          standardError = { method: "cluster", groups: value.clusterGroups };
        } else if (["HC0", "HC1", "HC2", "HC3"].includes(seMethod)) {
          standardError = {
            method: "robust",
            hcType: seMethod as RobustStandardErrorHcType,
          };
        } else {
          standardError = { method: "nonrobust" } as StandardErrorSettings;
        }
        const regressionResponse = await api.regression({
          tableName: value.tableName,
          dependentVariable: value.dependentVariable,
          explanatoryVariables: value.explanatoryVariables,
          hasConst: value.hasConst,
          missingValueHandling:
            value.missingValueHandling as MissingValueHandlingType,
          analysis: { method: "ols" },
          standardError,
        });

        if (regressionResponse.code === "OK" && regressionResponse.result) {
          const { resultId } = regressionResponse.result;
          const resultResponse = await api.getAnalysisResult(resultId);
          if (resultResponse.code === "OK" && resultResponse.result) {
            // APIレスポンス構造: { code: "OK", result: AnalysisResultDetail }
            // TypeScript生成型より1段浅いネスト
            const detail =
              resultResponse.result as unknown as AnalysisResultDetail;
            addResult(
              detail.regressionOutput as unknown as LinearRegressionResultType,
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
  const seMethod = useStore(form.store, (s) => s.values.standardErrorMethod);
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
      className="flex flex-col gap-3 h-full min-h-0"
    >
      {/* ── TOP: テーブル選択（全幅・コンパクト） ── */}
      <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm">
        <form.Field name="tableName">
          {(field) => (
            <div className="flex items-center gap-3">
              <label className="shrink-0 text-xs font-medium text-brand-text-main">
                {t("LinearRegressionForm.DataSource")}
              </label>
              <div className="flex-1">
                <Select
                  id="data-table"
                  value={field.state.value}
                  onValueChange={handleTableSelect}
                  disabled={isSubmitting}
                  error={field.state.meta.errors[0]?.toString()}
                  placeholder={t("LinearRegressionForm.SelectData")}
                >
                  {tableList.map((table, index) => (
                    <SelectItem key={index} value={table}>
                      {table}
                    </SelectItem>
                  ))}
                </Select>
              </div>
              {field.state.meta.errors[0] && (
                <p className="shrink-0 text-xs text-red-600">
                  {field.state.meta.errors[0].toString()}
                </p>
              )}
            </div>
          )}
        </form.Field>
      </div>

      {/* ── MIDDLE: 2ペイン（変数選択 + オプション） ── */}
      <div className="flex min-h-0 flex-1 gap-3">
        {/* 左: 変数選択（主役・flex-1） */}
        <div className="flex min-h-0 flex-1 flex-col gap-3">
          {/* 変数選択カード */}
          <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm">
            <h2 className="mb-2 shrink-0 text-sm font-bold leading-tight text-text-heading">
              {t("LinearRegressionForm.SelectVariables")}
            </h2>
            <div className="flex min-h-0 flex-1 gap-3">
              {/* 被説明変数 (1/3) */}
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
                    className="flex min-h-0 w-[33%] flex-col"
                  />
                )}
              </form.Field>

              {/* 縦区切り */}
              <div className="w-px shrink-0 bg-border-color" />

              {/* 説明変数 (2/3) */}
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
                    className="flex min-h-0 flex-1 flex-col"
                  />
                )}
              </form.Field>
            </div>
          </div>
        </div>

        {/* 右: 詳細オプション（脇役・w-56） */}
        <div className="flex w-56 shrink-0 flex-col">
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
                <div className="flex flex-col gap-3">
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
                          <SelectItem value="HC0">HC0</SelectItem>
                          <SelectItem value="HC1">HC1</SelectItem>
                          <SelectItem value="HC2">HC2</SelectItem>
                          <SelectItem value="HC3">HC3</SelectItem>
                          <SelectItem value="hac">
                            {t("LinearRegressionForm.StandardError_hac")}
                          </SelectItem>
                          <SelectItem value="cluster">
                            {t("LinearRegressionForm.StandardError_cluster")}
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
                          onValueChange={(v) =>
                            field.handleChange(v === "true")
                          }
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

                  {/* HAC 追加パラメータ */}
                  {seMethod === "hac" && (
                    <div className="rounded-lg border border-border-color bg-secondary/50 p-2">
                      <form.Field name="hacMaxlags">
                        {(field) => (
                          <FormField
                            label={t("LinearRegressionForm.HacMaxlags")}
                            htmlFor="hac-maxlags"
                          >
                            <InputText
                              id="hac-maxlags"
                              type="number"
                              value={field.state.value.toString()}
                              onChange={(e) =>
                                field.handleChange(
                                  parseInt(e.target.value) || 0,
                                )
                              }
                              onBlur={field.handleBlur}
                              disabled={isSubmitting}
                            />
                          </FormField>
                        )}
                      </form.Field>
                    </div>
                  )}

                  {/* Cluster 追加パラメータ */}
                  {seMethod === "cluster" && (
                    <div className="rounded-lg border border-border-color bg-secondary/50 p-2">
                      <form.Field name="clusterGroups">
                        {(field) => (
                          <FormField
                            label={t("LinearRegressionForm.ClusterGroups")}
                            htmlFor="cluster-groups"
                          >
                            <div className="max-h-32 overflow-y-auto rounded-md border border-border-color bg-white p-1.5">
                              {columnList.length === 0 ? (
                                <p className="text-xs text-brand-text-main/60">
                                  {t("Common.NoColumnsAvailable")}
                                </p>
                              ) : (
                                columnList.map((col) => (
                                  <label
                                    key={col.name}
                                    className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-xs hover:bg-secondary"
                                  >
                                    <input
                                      type="checkbox"
                                      className="h-3.5 w-3.5 rounded border-gray-300 text-accent focus:ring-accent"
                                      checked={field.state.value.includes(
                                        col.name,
                                      )}
                                      onChange={() => {
                                        const next = field.state.value.includes(
                                          col.name,
                                        )
                                          ? field.state.value.filter(
                                              (v) => v !== col.name,
                                            )
                                          : [...field.state.value, col.name];
                                        field.handleChange(next);
                                      }}
                                      disabled={isSubmitting}
                                    />
                                    <span className="text-brand-text-main">
                                      {col.name}
                                    </span>
                                  </label>
                                ))
                              )}
                            </div>
                          </FormField>
                        )}
                      </form.Field>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
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
