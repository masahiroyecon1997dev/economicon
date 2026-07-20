import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail, StandardErrorSettings } from "@/api/model";
import {
  MissingValueHandlingType,
  RobustStandardErrorHcType,
} from "@/api/model";
import { InputText } from "@/components/atoms/Input/InputText";
import { SearchableSelect } from "@/components/atoms/Input/SearchableSelect";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { AnalysisOptionsCard } from "@/components/molecules/Card/AnalysisOptionsCard";
import { ExplainerButton } from "@/components/molecules/Dialog/ExplainerButton";
import { VariableSelectorField } from "@/components/molecules/Field/VariableSelectorField";
import { FormField } from "@/components/molecules/Form/FormField";
import { AnalysisNoTablesState } from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { createFieldError } from "@/lib/utils/formHelpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useForm, useStore } from "@tanstack/react-form";
import { HelpCircle } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const TIME_COLUMN_NONE = "";

type RERegressionFormProps = {
  onCancel: () => void;
};

export const RERegressionForm = ({ onCancel }: RERegressionFormProps) => {
  const { t } = useTranslation();
  const tErr = createFieldError(t);
  const tableList = useTableListStore((state) => state.tableList);
  const navigateToShell = useCurrentPageStore((state) => state.navigateToShell);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const safeInitialTable =
    activeTableName && tableList.includes(activeTableName)
      ? activeTableName
      : (tableList[0] ?? "");
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
      initialSelectedTableName: safeInitialTable,
    });
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);

  const form = useForm({
    defaultValues: {
      tableName: selectedTableName,
      resultName: "",
      description: "",
      dependentVariable: "",
      explanatoryVariables: [] as string[],
      entityIdColumn: "",
      timeColumn: TIME_COLUMN_NONE,
      missingValueHandling: MissingValueHandlingType.remove as
        | "ignore"
        | "remove"
        | "error",
      standardError: { method: "nonrobust" } as StandardErrorSettings,
    },
    validators: {
      onSubmit: z.object({
        tableName: z.string().min(1, t("ValidationMessages.DataNameSelect")),
        resultName: z.string(),
        description: z.string(),
        dependentVariable: z
          .string()
          .min(1, t("ValidationMessages.DependentVariableRequired")),
        explanatoryVariables: z.array(z.string().min(1)),
        entityIdColumn: z
          .string()
          .min(1, t("ValidationMessages.EntityIdColumnRequired")),
        timeColumn: z.string(),
        missingValueHandling: z.enum(["ignore", "remove", "error"] as const),
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
          hasConst: true,
          missingValueHandling:
            value.missingValueHandling as MissingValueHandlingType,
          analysis: {
            method: "re" as const,
            entityIdColumn: value.entityIdColumn,
            timeColumn:
              value.timeColumn === TIME_COLUMN_NONE ? null : value.timeColumn,
          },
          standardError: value.standardError,
        });

        if (regressionResponse.code === "OK" && regressionResponse.result) {
          const { resultId } = regressionResponse.result;
          const resultResponse = await api.getAnalysisResult(resultId);
          if (resultResponse.code === "OK" && resultResponse.result) {
            const detail: AnalysisResultDetail = resultResponse.result;
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
  const explanatoryVariables = useStore(
    form.store,
    (s) => s.values.explanatoryVariables,
  );
  const entityIdColumn = useStore(form.store, (s) => s.values.entityIdColumn);
  const timeColumn = useStore(form.store, (s) => s.values.timeColumn);
  const [optionsOpen, setOptionsOpen] = useState(false);

  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    form.setFieldValue("tableName", value);
    form.setFieldValue("dependentVariable", "");
    form.setFieldValue("explanatoryVariables", []);
    form.setFieldValue("entityIdColumn", "");
    form.setFieldValue("timeColumn", TIME_COLUMN_NONE);
  };

  // パネル列（entityIdColumn / timeColumn）は変数選択から除外
  const panelColumns = [entityIdColumn, timeColumn].filter(
    (c): c is string => c !== "" && c !== TIME_COLUMN_NONE,
  );

  return (
    <PageLayout
      title={t("RERegressionForm.Title")}
      description={t("RERegressionForm.Description")}
      titleAction={
        <ExplainerButton
          explainerKey="fe_method"
          aria-label={t("RERegressionForm.MethodExplainerButtonLabel")}
          data-testid="re-method-explainer-btn"
        >
          <HelpCircle className="h-4 w-4" aria-hidden="true" />
        </ExplainerButton>
      }
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          onCancel={onCancel}
          onSelect={() => navigateToShell("ImportDataFile")}
        />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            void form.handleSubmit();
          }}
          className="flex min-h-0 flex-1 flex-col gap-3"
          data-testid="re-regression-form"
        >
          {/* ── データ選択 ── */}
          <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <form.Field name="tableName">
              {(field) => (
                <div className="flex items-center gap-3">
                  <label className="shrink-0 text-xs font-medium text-brand-text-main">
                    {t("LinearRegressionForm.DataSource")}
                  </label>
                  <div className="flex-1">
                    <Select
                      id="re-data-table"
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

          <div className="flex min-h-0 flex-1 gap-3">
            {/* ── 左カラム: 変数設定 ── */}
            <div className="flex min-h-0 flex-1 flex-col gap-3">
              {/* 変数選択カード */}
              <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h2 className="mb-2 shrink-0 text-sm font-bold leading-tight text-text-heading">
                  {t("LinearRegressionForm.SelectVariables")}
                </h2>
                <div className="flex min-h-0 flex-1 flex-col gap-3">
                  {/* 被説明変数 */}
                  <form.Field name="dependentVariable">
                    {(field) => (
                      <FormField
                        label={t("LinearRegressionForm.DependentVariable")}
                        htmlFor="re-dependent-variable"
                        error={tErr(
                          field.state.meta.errors,
                          "ValidationMessages.DependentVariableRequired",
                        )}
                      >
                        <SearchableSelect
                          id="re-dependent-variable"
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
                          options={columnList
                            .filter(
                              (col) =>
                                !explanatoryVariables.includes(col.name) &&
                                !panelColumns.includes(col.name),
                            )
                            .map((col) => ({
                              value: col.name,
                              label: col.name,
                            }))}
                        />
                      </FormField>
                    )}
                  </form.Field>

                  {/* 説明変数 */}
                  <form.Field name="explanatoryVariables">
                    {(field) => (
                      <VariableSelectorField
                        label={t("LinearRegressionForm.ExplanatoryVariables")}
                        description={t(
                          "LinearRegressionForm.ExplanatoryVariablesDescription",
                        )}
                        mode="multiple"
                        columns={columnList.filter(
                          (col) =>
                            col.name !== dependentVariable &&
                            !panelColumns.includes(col.name),
                        )}
                        selectedValues={field.state.value}
                        onMultipleChange={(v) => field.handleChange(v)}
                        disabled={isSubmitting}
                        name="explanatoryVariables"
                        className="flex flex-col"
                      />
                    )}
                  </form.Field>

                  <div className="border-t border-border-color" />

                  {/* パネル設定 */}
                  <div className="flex flex-col gap-2">
                    <h3 className="text-xs font-semibold text-text-heading">
                      {t("FERegressionForm.PanelSettings")}
                    </h3>

                    {/* 個体ID列 */}
                    <form.Field name="entityIdColumn">
                      {(field) => (
                        <FormField
                          label={t("FERegressionForm.EntityIdColumn")}
                          htmlFor="re-entity-id-column"
                          error={tErr(
                            field.state.meta.errors,
                            "ValidationMessages.EntityIdColumnRequired",
                          )}
                        >
                          <SearchableSelect
                            id="re-entity-id-column"
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
                              if (
                                form.store.state.values.dependentVariable === v
                              ) {
                                form.setFieldValue("dependentVariable", "");
                              }
                            }}
                            disabled={isSubmitting}
                            placeholder={t(
                              "LinearRegressionForm.SelectVariable",
                            )}
                            error={tErr(
                              field.state.meta.errors,
                              "ValidationMessages.EntityIdColumnRequired",
                            )}
                            options={columnList
                              .filter(
                                (col) =>
                                  col.name !== dependentVariable &&
                                  !explanatoryVariables.includes(col.name) &&
                                  col.name !== timeColumn,
                              )
                              .map((col) => ({
                                value: col.name,
                                label: col.name,
                              }))}
                          />
                        </FormField>
                      )}
                    </form.Field>

                    {/* 時間列 */}
                    <form.Field name="timeColumn">
                      {(field) => (
                        <FormField
                          label={t("FERegressionForm.TimeColumn")}
                          htmlFor="re-time-column"
                        >
                          <SearchableSelect
                            id="re-time-column"
                            value={field.state.value}
                            onValueChange={(v) => {
                              field.handleChange(v);
                              const currentExp =
                                form.store.state.values.explanatoryVariables;
                              if (
                                v !== TIME_COLUMN_NONE &&
                                currentExp.includes(v)
                              ) {
                                form.setFieldValue(
                                  "explanatoryVariables",
                                  currentExp.filter((x: string) => x !== v),
                                );
                              }
                            }}
                            disabled={isSubmitting}
                            placeholder={t("FERegressionForm.TimeColumnNone")}
                            options={[
                              {
                                value: TIME_COLUMN_NONE,
                                label: t("FERegressionForm.TimeColumnNone"),
                              },
                              ...columnList
                                .filter(
                                  (col) =>
                                    col.name !== dependentVariable &&
                                    !explanatoryVariables.includes(col.name) &&
                                    col.name !== entityIdColumn,
                                )
                                .map((col) => ({
                                  value: col.name,
                                  label: col.name,
                                })),
                            ]}
                          />
                        </FormField>
                      )}
                    </form.Field>
                  </div>
                </div>
              </div>

              {/* 実行ボタン */}
              <ActionButtonBar
                cancelText={t("Common.Cancel")}
                selectText={
                  isSubmitting
                    ? t("RERegressionForm.Processing")
                    : t("RERegressionForm.RunAnalysis")
                }
                onCancel={onCancel}
                onSelect={() => {}}
                onSelectType="submit"
                isLoading={isSubmitting}
              />
            </div>

            {/* ── 右カラム: 詳細オプション ── */}
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
                      return t("RERegressionForm.AdvancedOptionsSummary", {
                        se: t(
                          `LinearRegressionForm.StandardError_${seDisplay}`,
                        ),
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
                              htmlFor="re-standard-error-method"
                            >
                              {t("LinearRegressionForm.StandardErrorMethod")}
                            </label>
                            <ExplainerButton
                              explainerKey={
                                ["HC0", "HC1", "HC2", "HC3"].includes(seMethod)
                                  ? "ols_se_robust"
                                  : seMethod === "hac"
                                    ? "ols_se_hac"
                                    : seMethod === "cluster"
                                      ? "ols_se_cluster"
                                      : "ols_se_nonrobust"
                              }
                              aria-label={t(
                                "LinearRegressionForm.SEExplainerButtonLabel",
                              )}
                              data-testid="se-method-explainer-btn"
                            >
                              <HelpCircle
                                className="h-3.5 w-3.5"
                                aria-hidden="true"
                              />
                            </ExplainerButton>
                          </div>
                          <Select
                            id="re-standard-error-method"
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
                              {t(
                                "LinearRegressionForm.StandardError_nonrobust",
                              )}
                            </SelectItem>
                            <SelectItem value="HC1">HC1 (robust)</SelectItem>
                            <SelectItem value="HC0">HC0</SelectItem>
                            <SelectItem value="HC2">HC2</SelectItem>
                            <SelectItem value="HC3">HC3</SelectItem>
                            <SelectItem value="hac">
                              {t("LinearRegressionForm.StandardError_hac")}
                            </SelectItem>
                            <SelectItem value="cluster">
                              {t("LinearRegressionForm.StandardError_cluster")}
                            </SelectItem>
                          </Select>

                          {/* HAC maxlags */}
                          {se.method === "hac" && (
                            <div className="mt-1">
                              <label className="block text-xs text-gray-600 dark:text-gray-400">
                                {t("LinearRegressionForm.HacMaxlags")}
                              </label>
                              <InputText
                                type="number"
                                value={String(
                                  (
                                    se as Extract<
                                      StandardErrorSettings,
                                      { method: "hac" }
                                    >
                                  ).maxlags ?? 1,
                                )}
                                onChange={(e) => {
                                  const v = parseInt(e.target.value, 10);
                                  form.setFieldValue("standardError", {
                                    method: "hac",
                                    maxlags: isNaN(v) ? 1 : Math.max(0, v),
                                  });
                                }}
                                disabled={isSubmitting}
                                min={0}
                              />
                            </div>
                          )}

                          {/* Cluster groups */}
                          {se.method === "cluster" && (
                            <div className="mt-1">
                              <label className="block text-xs text-gray-600 dark:text-gray-400">
                                {t("LinearRegressionForm.ClusterGroups")}
                              </label>
                              <VariableSelectorField
                                label=""
                                mode="multiple"
                                columns={columnList}
                                selectedValues={
                                  (
                                    se as Extract<
                                      StandardErrorSettings,
                                      { method: "cluster" }
                                    >
                                  ).groups ?? []
                                }
                                onMultipleChange={(v) => {
                                  form.setFieldValue("standardError", {
                                    method: "cluster",
                                    groups: v,
                                  });
                                }}
                                disabled={isSubmitting}
                                name="clusterGroups"
                              />
                            </div>
                          )}
                        </div>
                      );
                    }}
                  </form.Field>

                  {/* 欠損値処理 */}
                  <form.Field name="missingValueHandling">
                    {(field) => (
                      <FormField
                        label={t("LinearRegressionForm.MissingValueHandling")}
                        htmlFor="re-missing-value"
                      >
                        <Select
                          id="re-missing-value"
                          value={field.state.value}
                          onValueChange={(v) =>
                            field.handleChange(
                              v as "ignore" | "remove" | "error",
                            )
                          }
                          disabled={isSubmitting}
                        >
                          <SelectItem value="remove">
                            {t("LinearRegressionForm.MissingValue_remove")}
                          </SelectItem>
                          <SelectItem value="ignore">
                            {t("LinearRegressionForm.MissingValue_ignore")}
                          </SelectItem>
                          <SelectItem value="error">
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
        </form>
      )}
    </PageLayout>
  );
};
