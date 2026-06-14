import { getEconomiconAppAPI } from "@/api/endpoints";
import { ConfidenceIntervalStatisticsType } from "@/api/model";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { FormField } from "@/components/molecules/Form/FormField";
import {
  AnalysisEmptyState,
  AnalysisNoTablesState,
} from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { openExplainerDialog } from "@/stores/explainerDialog";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useForm, useStore } from "@tanstack/react-form";
import { Info, Loader2, SearchX } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const STATISTIC_TYPES = [
  ConfidenceIntervalStatisticsType.mean,
  ConfidenceIntervalStatisticsType.median,
  ConfidenceIntervalStatisticsType.proportion,
  ConfidenceIntervalStatisticsType.variance,
  ConfidenceIntervalStatisticsType.standard_deviation,
] as const;

const CONFIDENCE_LEVEL_PRESETS = [
  { value: "0.90", labelKey: "ConfidenceIntervalView.ConfidenceLevel_090" },
  { value: "0.95", labelKey: "ConfidenceIntervalView.ConfidenceLevel_095" },
  { value: "0.99", labelKey: "ConfidenceIntervalView.ConfidenceLevel_099" },
] as const;

const createSchema = (t: (key: string) => string) =>
  z
    .object({
      tableName: z
        .string()
        .min(1, t("ConfidenceIntervalView.ErrorDataRequired")),
      columnName: z
        .string()
        .min(1, t("ConfidenceIntervalView.ErrorColumnRequired")),
      statisticType: z
        .string()
        .min(1, t("ConfidenceIntervalView.ErrorStatisticTypeRequired")),
      confidenceLevelMode: z.enum(["select", "manual"]),
      confidenceLevelSelect: z.string(),
      confidenceLevelManual: z.string(),
    })
    .superRefine((val, ctx) => {
      if (val.confidenceLevelMode === "manual") {
        const num = Number(val.confidenceLevelManual);
        if (isNaN(num) || num <= 0 || num >= 1) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: t("ConfidenceIntervalView.ErrorConfidenceLevelInvalid"),
            path: ["confidenceLevelManual"],
          });
        }
      }
    });

type ConfidenceIntervalFormProps = {
  onCancel: () => void;
};

export const ConfidenceIntervalForm = ({
  onCancel,
}: ConfidenceIntervalFormProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const { selectedTableName, setSelectedTableName, columnList, isLoading } =
    useTableColumnLoader({ numericOnly: true, autoLoadOnMount: true });
  const navigateToShell = useCurrentPageStore((state) => state.navigateToShell);
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);
  const [levelMode, setLevelMode] = useState<"select" | "manual">("select");

  const form = useForm({
    defaultValues: {
      tableName: selectedTableName,
      columnName: "",
      statisticType: "",
      confidenceLevelMode: "select" as "select" | "manual",
      confidenceLevelSelect: "0.95",
      confidenceLevelManual: "",
    },
    validators: {
      onSubmit: createSchema(t),
    },
    onSubmit: async ({ value }) => {
      const confidenceLevel =
        value.confidenceLevelMode === "manual"
          ? Number(value.confidenceLevelManual)
          : Number(value.confidenceLevelSelect);
      try {
        const api = getEconomiconAppAPI();
        const response = await api.confidenceInterval({
          tableName: value.tableName,
          columnName: value.columnName,
          statisticType:
            value.statisticType as ConfidenceIntervalStatisticsType,
          confidenceLevel,
        });
        if (response.code === "OK" && response.result) {
          const { resultId } = response.result;
          const detailResponse = await api.getAnalysisResult(resultId);
          if (detailResponse.code === "OK") {
            openResultTab(detailResponse.result);
            await useAnalysisResultsStore.getState().fetchSummaries();
            return;
          }

          await showMessageDialog(
            t("Error.Error"),
            buildResponseErrorMessage(
              detailResponse,
              t("Error.UnexpectedError"),
            ),
          );
          return;
        }

        await showMessageDialog(
          t("Error.Error"),
          buildResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          buildCaughtErrorMessage(error, t("Error.UnexpectedError")),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  if (tableList.length === 0) {
    return (
      <AnalysisNoTablesState
        className="flex-1"
        onCancel={onCancel}
        onSelect={() => navigateToShell("ImportDataFile")}
      />
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
      className="flex flex-col flex-1 min-h-0"
    >
      <div className="app-scrollbar flex flex-col gap-4 max-w-lg overflow-y-auto flex-1 min-h-0 pb-2 px-1">
        {/* 対象データ */}
        <form.Field name="tableName">
          {(field) => (
            <FormField
              label={t("ConfidenceIntervalView.DataLabel")}
              htmlFor="ci-table-name"
              error={extractFieldError(field.state.meta.errors)}
            >
              <Select
                id="ci-table-name"
                value={field.state.value}
                placeholder={t("ConfidenceIntervalView.SelectData")}
                error={extractFieldError(field.state.meta.errors)}
                onValueChange={(v) => {
                  field.handleChange(v);
                  setSelectedTableName(v);
                  form.setFieldValue("columnName", "");
                }}
              >
                {tableList.map((tbl) => (
                  <SelectItem key={tbl} value={tbl}>
                    {tbl}
                  </SelectItem>
                ))}
              </Select>
            </FormField>
          )}
        </form.Field>

        {/* 対象列 */}
        <form.Field name="columnName">
          {(field) => (
            <FormField
              label={t("ConfidenceIntervalView.ColumnLabel")}
              htmlFor="ci-column-name"
              error={extractFieldError(field.state.meta.errors)}
            >
              {selectedTableName !== "" && isLoading ? (
                <AnalysisEmptyState
                  compact
                  testId="confidence-interval-loading-columns-state"
                  icon={<Loader2 className="h-6 w-6 animate-spin" />}
                  title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                  description={t(
                    "AnalysisEmptyState.LoadingColumnsDescription",
                  )}
                />
              ) : selectedTableName !== "" && columnList.length === 0 ? (
                <AnalysisEmptyState
                  compact
                  testId="confidence-interval-no-columns-state"
                  icon={<SearchX className="h-6 w-6" />}
                  title={t("AnalysisEmptyState.NoEligibleColumnsTitle")}
                  description={t("ConfidenceIntervalView.NoColumns")}
                  hint={t("AnalysisEmptyState.NoEligibleColumnsHint")}
                />
              ) : (
                <Select
                  id="ci-column-name"
                  value={field.state.value}
                  placeholder={t("ConfidenceIntervalView.SelectColumn")}
                  error={extractFieldError(field.state.meta.errors)}
                  onValueChange={field.handleChange}
                  disabled={columnList.length === 0}
                >
                  {columnList.map((col) => (
                    <SelectItem key={col.name} value={col.name}>
                      {col.name}
                    </SelectItem>
                  ))}
                </Select>
              )}
            </FormField>
          )}
        </form.Field>

        {/* 統計量タイプ */}
        <form.Field name="statisticType">
          {(field) => (
            <div className="space-y-1">
              {/* ラベル行: テキスト + Info アイコン */}
              <div className="flex items-center gap-1.5">
                <label
                  className="block text-sm font-medium text-gray-700"
                  htmlFor="ci-statistic-type"
                >
                  {t("ConfidenceIntervalView.StatisticTypeLabel")}
                </label>
                {field.state.value && (
                  <button
                    type="button"
                    aria-label={t(
                      "ConfidenceIntervalView.StatisticTypeInfoLabel",
                    )}
                    onClick={() => openExplainerDialog(field.state.value)}
                    className="text-gray-400 hover:text-brand-accent transition-colors"
                    data-testid="statistic-type-info-btn"
                  >
                    <Info size={14} aria-hidden="true" />
                  </button>
                )}
              </div>
              <Select
                id="ci-statistic-type"
                value={field.state.value}
                placeholder={t("ConfidenceIntervalView.SelectStatisticType")}
                error={extractFieldError(field.state.meta.errors)}
                onValueChange={field.handleChange}
              >
                {STATISTIC_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {t(`ConfidenceIntervalView.StatisticType_${type}`)}
                  </SelectItem>
                ))}
              </Select>
              {extractFieldError(field.state.meta.errors) && (
                <p className="text-xs text-red-600 mt-0.5">
                  {extractFieldError(field.state.meta.errors)}
                </p>
              )}
            </div>
          )}
        </form.Field>

        {/* 信頼水準 */}
        <FormField label={t("ConfidenceIntervalView.ConfidenceLevelLabel")}>
          {/* モード切り替えトグル */}
          <div className="flex gap-2 mb-2">
            <button
              type="button"
              onClick={() => {
                setLevelMode("select");
                form.setFieldValue("confidenceLevelMode", "select");
              }}
              className={cn(
                "px-3 py-1 text-xs rounded-md border transition-colors",
                levelMode === "select"
                  ? "bg-brand-accent text-white border-brand-accent"
                  : "bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500",
              )}
            >
              {t("ConfidenceIntervalView.ConfidenceLevelModeSelect")}
            </button>
            <button
              type="button"
              onClick={() => {
                setLevelMode("manual");
                form.setFieldValue("confidenceLevelMode", "manual");
              }}
              className={cn(
                "px-3 py-1 text-xs rounded-md border transition-colors",
                levelMode === "manual"
                  ? "bg-brand-accent text-white border-brand-accent"
                  : "bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500",
              )}
            >
              {t("ConfidenceIntervalView.ConfidenceLevelModeManual")}
            </button>
          </div>

          {levelMode === "select" ? (
            <form.Field name="confidenceLevelSelect">
              {(field) => (
                <Select
                  id="ci-confidence-level-select"
                  value={field.state.value}
                  onValueChange={field.handleChange}
                >
                  {CONFIDENCE_LEVEL_PRESETS.map((preset) => (
                    <SelectItem key={preset.value} value={preset.value}>
                      {t(preset.labelKey)}
                    </SelectItem>
                  ))}
                </Select>
              )}
            </form.Field>
          ) : (
            <form.Field name="confidenceLevelManual">
              {(field) => (
                <>
                  <InputText
                    id="ci-confidence-level-manual"
                    type="number"
                    step="0.01"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    onBlur={field.handleBlur}
                    placeholder={t(
                      "ConfidenceIntervalView.ConfidenceLevelManualPlaceholder",
                    )}
                    error={extractFieldError(field.state.meta.errors)}
                  />
                  {extractFieldError(field.state.meta.errors) && (
                    <p className="text-xs text-red-600 mt-0.5">
                      {extractFieldError(field.state.meta.errors)}
                    </p>
                  )}
                </>
              )}
            </form.Field>
          )}
        </FormField>
      </div>

      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isSubmitting
            ? t("ConfidenceIntervalView.Processing")
            : t("ConfidenceIntervalView.RunCalculation")
        }
        onCancel={onCancel}
        onSelect={() => {}}
        onSelectType="submit"
        disabled={isSubmitting}
        isLoading={isSubmitting}
      />
    </form>
  );
};
