import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail, StandardErrorSettings } from "@/api/model";
import {
  MissingValueHandlingType,
  RobustStandardErrorHcType,
} from "@/api/model";
import {
  regressionBodyDescriptionMax,
  regressionBodyResultNameMax,
} from "@/api/zod/analysis/analysis";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { Tooltip } from "@/components/atoms/Tooltip/Tooltip";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { AnalysisOptionsCard } from "@/components/molecules/Card/AnalysisOptionsCard";
import { VariableSelectorField } from "@/components/molecules/Field/VariableSelectorField";
import { FormField } from "@/components/molecules/Form/FormField";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { createFieldError } from "@/lib/utils/formHelpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useForm, useStore } from "@tanstack/react-form";
import { HelpCircle } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

type LinearRegressionFormProps = {
  onCancel: () => void;
};

export const LinearRegressionForm = ({
  onCancel,
}: LinearRegressionFormProps) => {
  const { t } = useTranslation();
  const tErr = createFieldError(t);
  const tableList = useTableListStore((state) => state.tableList);
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
    });
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);
  const closeActiveWorkTab = useWorkspaceTabsStore(
    (state) => state.closeActiveWorkTab,
  );

  const form = useForm({
    defaultValues: {
      tableName: selectedTableName,
      resultName: "",
      description: "",
      dependentVariable: "",
      explanatoryVariables: [] as string[],
      hasConst: true,
      missingValueHandling: MissingValueHandlingType.remove as
        | "ignore"
        | "remove"
        | "error",
      analysis: { method: "ols" } as const,
      standardError: { method: "nonrobust" } as StandardErrorSettings,
    },
    validators: {
      onSubmit: z.object({
        tableName: z.string().min(1, t("ValidationMessages.DataNameSelect")),
        resultName: z.string().max(regressionBodyResultNameMax),
        description: z.string().max(regressionBodyDescriptionMax),
        dependentVariable: z
          .string()
          .min(1, t("ValidationMessages.DependentVariableRequired")),
        explanatoryVariables: z
          .array(z.string().min(1))
          .min(1, t("ValidationMessages.ExplanatoryVariablesRequired")),
        hasConst: z.boolean(),
        missingValueHandling: z.enum(["ignore", "remove", "error"] as const),
        analysis: z.object({ method: z.literal("ols") }),
        standardError: z.custom<StandardErrorSettings>(),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        const api = getEconomiconAppAPI();
        const regressionResponse = await api.regression({
          tableName: value.tableName,
          resultName: value.resultName,
          description: value.description,
          dependentVariable: value.dependentVariable,
          explanatoryVariables: value.explanatoryVariables,
          hasConst: value.hasConst,
          missingValueHandling:
            value.missingValueHandling as MissingValueHandlingType,
          analysis: value.analysis,
          standardError: value.standardError,
        });

        if (regressionResponse.code === "OK" && regressionResponse.result) {
          const { resultId } = regressionResponse.result;
          const resultResponse = await api.getAnalysisResult(resultId);
          if (resultResponse.code === "OK" && resultResponse.result) {
            const detail: AnalysisResultDetail = resultResponse.result;
            closeActiveWorkTab();
            openResultTab(detail);
            await useAnalysisResultsStore.getState().fetchSummaries();
            return;
          }
          await showMessageDialog(
            t("Error.Error"),
            buildResponseErrorMessage(
              resultResponse,
              t("Error.UnexpectedError"),
            ),
          );
        } else {
          await showMessageDialog(
            t("Error.Error"),
            buildResponseErrorMessage(
              regressionResponse,
              t("Error.UnexpectedError"),
            ),
          );
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          buildCaughtErrorMessage(error, t("Error.UnexpectedError")),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const seMethod = useStore(form.store, (s) => {
    const se = s.values.standardError;
    if (se.method === "robust") {
      return (
        (se as Extract<StandardErrorSettings, { method: "robust" }>).hcType ??
        "HC1"
      );
    }
    return se.method;
  });
  const dependentVariable = useStore(
    form.store,
    (s) => s.values.dependentVariable,
  );
  const [optionsOpen, setOptionsOpen] = useState(false);

  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    form.setFieldValue("tableName", value);
    form.setFieldValue("dependentVariable", "");
    form.setFieldValue("explanatoryVariables", []);
  };

  return (
    <PageLayout
      title={t("LinearRegressionForm.Title")}
      description={t("LinearRegressionForm.Description")}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex min-h-0 flex-1 flex-col gap-3"
      >
        {/* ── TOP: テーブル選択（幅コンパクト）── */}
        <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
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
                    error={tErr(
                      field.state.meta.errors,
                      "ValidationMessages.DataNameSelect",
                    )}
                  >
                    {tableList.map((table, index) => (
                      <SelectItem key={index} value={table}>
                        {table}
                      </SelectItem>
                    ))}
                  </Select>
                </div>
                {tErr(
                  field.state.meta.errors,
                  "ValidationMessages.DataNameSelect",
                ) && (
                  <p className="shrink-0 text-xs text-red-600">
                    {tErr(
                      field.state.meta.errors,
                      "ValidationMessages.DataNameSelect",
                    )}
                  </p>
                )}
              </div>
            )}
          </form.Field>
        </div>

        {/* ── MIDDLE: 2ペイン（変数選択 + オプション）── */}
        <div className="flex min-h-0 flex-1 gap-3">
          <div className="flex min-h-0 flex-1 flex-col gap-3">
            <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <h2 className="mb-2 shrink-0 text-sm font-bold leading-tight text-text-heading">
                {t("LinearRegressionForm.SelectVariables")}
              </h2>
              <div className="flex min-h-0 flex-1 flex-col gap-3">
                <form.Field name="dependentVariable">
                  {(field) => (
                    <FormField
                      label={t("LinearRegressionForm.DependentVariable")}
                      htmlFor="dependent-variable"
                      error={tErr(
                        field.state.meta.errors,
                        "ValidationMessages.DependentVariableRequired",
                      )}
                    >
                      <Select
                        id="dependent-variable"
                        value={field.state.value}
                        onValueChange={(v) => {
                          field.handleChange(v);
                          const currentExp =
                            form.store.state.values.explanatoryVariables;
                          if (currentExp.includes(v)) {
                            form.setFieldValue(
                              "explanatoryVariables",
                              currentExp.filter((x: string) => x !== v),
                            );
                          }
                        }}
                        disabled={isSubmitting}
                        placeholder={t("LinearRegressionForm.SelectVariable")}
                        error={tErr(
                          field.state.meta.errors,
                          "ValidationMessages.DependentVariableRequired",
                        )}
                      >
                        {columnList.map((col) => (
                          <SelectItem key={col.name} value={col.name}>
                            {col.name}
                          </SelectItem>
                        ))}
                      </Select>
                    </FormField>
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
                      columns={columnList.filter(
                        (col) => col.name !== dependentVariable,
                      )}
                      selectedValues={field.state.value}
                      onMultipleChange={(v) => field.handleChange(v)}
                      error={tErr(
                        field.state.meta.errors,
                        "ValidationMessages.ExplanatoryVariablesRequired",
                      )}
                      disabled={isSubmitting}
                      name="explanatoryVariables"
                      className="flex min-h-0 flex-1 flex-col"
                    />
                  )}
                </form.Field>
              </div>
            </div>
          </div>

          <div className="flex w-56 shrink-0 flex-col">
            <AnalysisOptionsCard
              title={t("LinearRegressionForm.AdvancedOptions")}
              open={optionsOpen}
              onToggle={() => setOptionsOpen((v) => !v)}
              summary={
                <form.Subscribe selector={(s) => s.values}>
                  {(values) => {
                    const se = values.standardError;
                    const seDisplay =
                      se.method === "robust"
                        ? ((
                            se as Extract<
                              StandardErrorSettings,
                              { method: "robust" }
                            >
                          ).hcType ?? "HC1")
                        : se.method;
                    return t("LinearRegressionForm.AdvancedOptionsSummary", {
                      se: t(`LinearRegressionForm.StandardError_${seDisplay}`),
                      const: values.hasConst
                        ? t("LinearRegressionForm.HasConstYes")
                        : t("LinearRegressionForm.HasConstNo"),
                      missing: t(
                        `LinearRegressionForm.MissingValue_${values.missingValueHandling}`,
                      ),
                    });
                  }}
                </form.Subscribe>
              }
            >
              <div className="flex flex-col gap-3">
                {/* 標準誤差 */}
                <form.Field name="standardError">
                  {(field) => {
                    const se = field.state.value;
                    const displayMethod =
                      se.method === "robust"
                        ? ((
                            se as Extract<
                              StandardErrorSettings,
                              { method: "robust" }
                            >
                          ).hcType ?? "HC1")
                        : se.method;
                    return (
                      <div className="space-y-1">
                        <div className="flex items-center gap-1">
                          <label
                            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                            htmlFor="standard-error-method"
                          >
                            {t("LinearRegressionForm.StandardErrorMethod")}
                          </label>
                          <Tooltip
                            content={t(
                              `LinearRegressionForm.SE_tooltip_${seMethod}`,
                            )}
                            position="right"
                            maxWidth={240}
                          >
                            <button
                              type="button"
                              className="text-brand-text-sub hover:text-brand-text-main"
                              aria-label={t(
                                "LinearRegressionForm.StandardErrorMethod",
                              )}
                            >
                              <HelpCircle className="h-3.5 w-3.5" />
                            </button>
                          </Tooltip>
                        </div>
                        <Select
                          id="standard-error-method"
                          value={displayMethod}
                          onValueChange={(v) => {
                            if (v === "hac") {
                              form.setFieldValue("standardError", {
                                method: "hac",
                                maxlags: 1,
                              });
                            } else if (v === "cluster") {
                              form.setFieldValue("standardError", {
                                method: "cluster",
                                groups: [],
                              });
                            } else if (
                              ["HC0", "HC1", "HC2", "HC3"].includes(v)
                            ) {
                              form.setFieldValue("standardError", {
                                method: "robust",
                                hcType: v as RobustStandardErrorHcType,
                              });
                            } else {
                              form.setFieldValue("standardError", {
                                method: "nonrobust",
                              });
                            }
                          }}
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

                        {/* ── HAC 標準誤差── */}
                        {se.method === "hac" && (
                          <div className="rounded-lg border border-border-color bg-secondary/50 p-2">
                            <FormField
                              label={t("LinearRegressionForm.HacMaxlags")}
                              htmlFor="hac-maxlags"
                            >
                              <InputText
                                id="hac-maxlags"
                                type="number"
                                value={(
                                  se as Extract<
                                    StandardErrorSettings,
                                    { method: "hac" }
                                  >
                                ).maxlags.toString()}
                                onChange={(e) => {
                                  const hacSe = se as Extract<
                                    StandardErrorSettings,
                                    { method: "hac" }
                                  >;
                                  field.handleChange({
                                    ...hacSe,
                                    maxlags: parseInt(e.target.value) || 0,
                                  });
                                }}
                                onBlur={field.handleBlur}
                                disabled={isSubmitting}
                              />
                            </FormField>
                          </div>
                        )}

                        {/* ── Cluster 標準誤差── */}
                        {se.method === "cluster" && (
                          <div className="rounded-lg border border-border-color bg-secondary/50 p-2">
                            <FormField
                              label={t("LinearRegressionForm.ClusterGroups")}
                              htmlFor="cluster-groups"
                            >
                              <div className="app-scrollbar max-h-32 overflow-y-auto rounded-md border border-border-color bg-white dark:bg-gray-800 p-1.5">
                                {columnList.length === 0 ? (
                                  <p className="text-xs text-brand-text-main/60">
                                    {t("Common.NoColumnsAvailable")}
                                  </p>
                                ) : (
                                  columnList.map((col) => {
                                    const clusterSe = se as Extract<
                                      StandardErrorSettings,
                                      { method: "cluster" }
                                    >;
                                    return (
                                      <label
                                        key={col.name}
                                        className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-xs hover:bg-secondary"
                                      >
                                        <input
                                          type="checkbox"
                                          className="h-3.5 w-3.5 rounded border-gray-300 text-accent focus:ring-accent"
                                          checked={clusterSe.groups.includes(
                                            col.name,
                                          )}
                                          onChange={() => {
                                            const next =
                                              clusterSe.groups.includes(
                                                col.name,
                                              )
                                                ? clusterSe.groups.filter(
                                                    (v) => v !== col.name,
                                                  )
                                                : [
                                                    ...clusterSe.groups,
                                                    col.name,
                                                  ];
                                            field.handleChange({
                                              ...clusterSe,
                                              groups: next,
                                            });
                                          }}
                                          disabled={isSubmitting}
                                        />
                                        <span className="text-brand-text-main">
                                          {col.name}
                                        </span>
                                      </label>
                                    );
                                  })
                                )}
                              </div>
                            </FormField>
                          </div>
                        )}
                      </div>
                    );
                  }}
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
            </AnalysisOptionsCard>
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
          isLoading={isSubmitting}
        />
      </form>
    </PageLayout>
  );
};
