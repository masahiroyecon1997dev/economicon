import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { CreateGroupStatisticsTableBody } from "@/api/zod/statistics/statistics";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { CheckboxTagGroup } from "@/components/molecules/Field/CheckboxTagGroup";
import { SelectAllBar } from "@/components/molecules/Field/SelectAllBar";
import { VariableSelectorField } from "@/components/molecules/Field/VariableSelectorField";
import { FormField } from "@/components/molecules/Form/FormField";
import {
  AnalysisEmptyState,
  AnalysisNoTablesState,
} from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "@/lib/utils/apiError";
import { createFieldError } from "@/lib/utils/formHelpers";
import { getTableInfo } from "@/lib/utils/internal";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { WorkspaceWorkTab } from "@/stores/workspaceTabs";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import type { ColumnType } from "@/types/commonTypes";
import { useForm, useStore } from "@tanstack/react-form";
import { Loader2, SearchX } from "lucide-react";
import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ALL_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.mode,
  DescriptiveStatisticType.variance,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
  DescriptiveStatisticType.range,
  DescriptiveStatisticType.iqr,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
  DescriptiveStatisticType.skewness,
  DescriptiveStatisticType.kurtosis,
  DescriptiveStatisticType.population_variance,
];

const DEFAULT_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
];

const isFloatColumn = (col: ColumnType): boolean =>
  col.type === "Float32" || col.type === "Float64";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type GroupStatisticsFormValues = {
  tableName: string;
  groupByColumns: string[];
  statColumns: string[];
  statistics: DescriptiveStatisticType[];
  newTableName: string;
};

type GroupStatisticsProps = {
  workTabId?: `work:GroupStatistics`;
  onSuccess?: (tableName: string) => void;
  onCancel?: () => void | Promise<void>;
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const GroupStatistics = ({
  workTabId,
  onSuccess,
  onCancel,
}: GroupStatisticsProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const addTableName = useTableListStore((s) => s.addTableName);
  const initialTableName = useTableInfosStore((s) => s.activeTableName) ?? "";
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const ensureWorkTabState = useWorkspaceTabsStore((s) => s.ensureWorkTabState);
  const updateWorkTabDraft = useWorkspaceTabsStore((s) => s.updateWorkTabDraft);
  const commitWorkTab = useWorkspaceTabsStore((s) => s.commitWorkTab);

  const persistedWorkTab = useWorkspaceTabsStore((state) =>
    workTabId
      ? (state.tabs.find(
          (
            tab,
          ): tab is WorkspaceWorkTab & {
            featureKey: "GroupStatistics";
            id: `work:GroupStatistics`;
          } =>
            tab.id === workTabId &&
            tab.kind === "work" &&
            tab.featureKey === "GroupStatistics",
        ) ?? null)
      : null,
  );

  const persistedDraft = persistedWorkTab?.draftValues as
    | GroupStatisticsFormValues
    | undefined;
  const shouldAutoSelectRef = useRef(!persistedDraft);

  const initialValues: GroupStatisticsFormValues = {
    tableName: persistedDraft?.tableName ?? initialTableName,
    groupByColumns: persistedDraft?.groupByColumns ?? [],
    statColumns: persistedDraft?.statColumns ?? [],
    statistics: persistedDraft?.statistics ?? DEFAULT_STAT_TYPES,
    newTableName: persistedDraft?.newTableName ?? "",
  };

  const {
    selectedTableName,
    setSelectedTableName,
    columnList,
    setColumnList,
    isLoading,
  } = useTableColumnLoader({
    numericOnly: false,
    autoLoadOnMount: true,
    initialSelectedTableName: initialValues.tableName,
  });

  const form = useForm({
    defaultValues: initialValues,
    validators: {
      onSubmit: CreateGroupStatisticsTableBody.required(),
    },
    onSubmit: async ({ value }) => {
      try {
        const api = getEconomiconAppAPI();
        // Preserve column order from columnList
        const orderedGroupBy = columnList
          .map((c) => c.name)
          .filter((n) => value.groupByColumns.includes(n));
        const orderedStat = columnList
          .map((c) => c.name)
          .filter((n) => value.statColumns.includes(n));
        const orderedStats = ALL_STAT_TYPES.filter((s) =>
          value.statistics.includes(s),
        );

        const submittedValues: GroupStatisticsFormValues = {
          ...value,
          groupByColumns: orderedGroupBy,
          statColumns: orderedStat,
          statistics: orderedStats,
          newTableName: value.newTableName.trim(),
        };

        const resp = await api.createGroupStatisticsTable({
          tableName: submittedValues.tableName,
          groupByColumns: submittedValues.groupByColumns,
          statColumns: submittedValues.statColumns,
          statistics: submittedValues.statistics,
          newTableName: submittedValues.newTableName,
        });

        if (resp.code === "OK") {
          const tableInfo = await getTableInfo(resp.result.tableName);
          addTableName(resp.result.tableName);
          addTableInfo(tableInfo);
          if (workTabId) {
            commitWorkTab(workTabId, submittedValues);
          }
          if (onSuccess) {
            onSuccess(resp.result.tableName);
          } else {
            setCurrentView("DataPreview");
          }
        } else {
          await showMessageDialog(
            t("Error.Error"),
            getResponseErrorMessage(resp, t("Error.UnexpectedError")),
          );
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          extractApiErrorMessage(error, t("Error.UnexpectedError")),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const formValues = useStore(form.store, (s) => s.values);

  // Columns that cannot be used as groupByColumns (Float32 / Float64)
  const floatColumnNames = new Set(
    columnList.filter(isFloatColumn).map((c) => c.name),
  );
  // Columns that cannot be used as statColumns (those already selected as groupByColumns)
  const groupByColumnSet = new Set(formValues.groupByColumns);

  // Reset auto-select flag on initial column load
  useEffect(() => {
    if (!shouldAutoSelectRef.current || columnList.length === 0) return;
    shouldAutoSelectRef.current = false;
  }, [columnList]);

  // Persist draft to work tab
  useEffect(() => {
    if (!workTabId) return;
    ensureWorkTabState(workTabId, formValues);
  }, [ensureWorkTabState, formValues, workTabId]);

  useEffect(() => {
    if (!workTabId) return;
    updateWorkTabDraft(workTabId, formValues);
  }, [formValues, updateWorkTabDraft, workTabId]);

  const handleTableSelect = (value: string) => {
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    shouldAutoSelectRef.current = !!value;
    form.setFieldValue("tableName", value);
    form.setFieldValue("groupByColumns", []);
    form.setFieldValue("statColumns", []);
  };

  const handleGroupByChange = (newGroupBy: string[]) => {
    form.setFieldValue("groupByColumns", newGroupBy);
    // Remove groupByColumns from statColumns to prevent overlap
    const filteredStatCols = formValues.statColumns.filter(
      (c) => !newGroupBy.includes(c),
    );
    form.setFieldValue("statColumns", filteredStatCols);
  };

  const toggleStat = (stat: DescriptiveStatisticType) => {
    const current = new Set(formValues.statistics);
    if (current.has(stat)) {
      current.delete(stat);
    } else {
      current.add(stat);
    }
    form.setFieldValue("statistics", [
      ...current,
    ] as DescriptiveStatisticType[]);
  };

  const handleCancel = () => {
    if (onCancel) {
      void onCancel();
      return;
    }
    setCurrentView("DataPreview");
  };

  const tErr = createFieldError(t);
  const checkedStats = new Set(formValues.statistics);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <PageLayout
      title={t("GroupStatistics.Title")}
      description={t("GroupStatistics.Description")}
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          className="flex-1"
          onCancel={handleCancel}
          onSelect={() => setCurrentView("ImportDataFile")}
        />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            void form.handleSubmit();
          }}
          className="flex min-h-0 flex-1 flex-col gap-3"
        >
          {/* ── TOP: テーブル選択（compact row）── */}
          <div className="shrink-0 rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <form.Field name="tableName">
              {(field) => (
                <div className="flex items-center gap-3">
                  <label className="shrink-0 text-xs font-medium text-brand-text-main">
                    {t("GroupStatistics.DataLabel")}
                  </label>
                  <div className="flex-1">
                    <Select
                      value={field.state.value}
                      onValueChange={handleTableSelect}
                      disabled={isSubmitting}
                      placeholder={t("GroupStatistics.SelectData")}
                      error={tErr(
                        field.state.meta.errors,
                        "GroupStatistics.ErrorDataRequired",
                      )}
                    >
                      {tableList.map((name) => (
                        <SelectItem key={name} value={name}>
                          {name}
                        </SelectItem>
                      ))}
                    </Select>
                  </div>
                </div>
              )}
            </form.Field>
          </div>

          {/* ── MIDDLE: 3 ペイン ── */}
          <div className="flex min-h-0 flex-1 gap-3">
            {/* 左: グループキー列 */}
            <div
              className="flex w-52 shrink-0 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800"
              data-testid="group-statistics-group-by-panel"
            >
              <div className="mb-2 shrink-0">
                <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                  {t("GroupStatistics.GroupByColumnsLabel")}
                </h2>
                <p className="mt-0.5 text-xs text-brand-text-sub">
                  {t("GroupStatistics.GroupByColumnsHint")}
                </p>
              </div>

              {!selectedTableName ? (
                <p className="text-sm text-brand-text-sub">
                  {t("GroupStatistics.SelectData")}
                </p>
              ) : isLoading ? (
                <AnalysisEmptyState
                  compact
                  testId="group-statistics-loading-columns"
                  icon={<Loader2 className="h-6 w-6 animate-spin" />}
                  title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                  description={t(
                    "AnalysisEmptyState.LoadingColumnsDescription",
                  )}
                  className="flex-1"
                />
              ) : columnList.filter((c) => !isFloatColumn(c)).length === 0 ? (
                <AnalysisEmptyState
                  compact
                  testId="group-statistics-no-groupby-columns"
                  icon={<SearchX className="h-6 w-6" />}
                  title={t("AnalysisEmptyState.NoEligibleColumnsTitle")}
                  description={t("GroupStatistics.NoGroupByColumns")}
                  hint={t("AnalysisEmptyState.NoEligibleColumnsHint")}
                  className="flex-1"
                />
              ) : (
                <form.Field name="groupByColumns">
                  {(field) => (
                    <VariableSelectorField
                      label=""
                      mode="multiple"
                      columns={columnList}
                      selectedValues={field.state.value}
                      onMultipleChange={handleGroupByChange}
                      disabledValues={floatColumnNames}
                      disabled={isSubmitting}
                      name="group-by-columns"
                      error={tErr(
                        field.state.meta.errors,
                        "GroupStatistics.ErrorGroupByRequired",
                      )}
                      className="min-h-0 flex-1"
                    />
                  )}
                </form.Field>
              )}
            </div>

            {/* 中: 集計列 */}
            <div
              className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800"
              data-testid="group-statistics-stat-columns-panel"
            >
              <div className="mb-2 shrink-0">
                <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                  {t("GroupStatistics.StatColumnsLabel")}
                </h2>
                <p className="mt-0.5 text-xs text-brand-text-sub">
                  {t("GroupStatistics.StatColumnsHint")}
                </p>
              </div>

              {!selectedTableName ? (
                <p className="text-sm text-brand-text-sub">
                  {t("GroupStatistics.SelectData")}
                </p>
              ) : isLoading ? (
                <AnalysisEmptyState
                  compact
                  testId="group-statistics-loading-stat-columns"
                  icon={<Loader2 className="h-6 w-6 animate-spin" />}
                  title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                  description={t(
                    "AnalysisEmptyState.LoadingColumnsDescription",
                  )}
                  className="flex-1"
                />
              ) : columnList.length === 0 ? (
                <AnalysisEmptyState
                  compact
                  testId="group-statistics-no-stat-columns"
                  icon={<SearchX className="h-6 w-6" />}
                  title={t("AnalysisEmptyState.NoEligibleColumnsTitle")}
                  description={t("GroupStatistics.NoStatColumns")}
                  hint={t("AnalysisEmptyState.NoEligibleColumnsHint")}
                  className="flex-1"
                />
              ) : (
                <form.Field name="statColumns">
                  {(field) => (
                    <VariableSelectorField
                      label=""
                      mode="multiple"
                      columns={columnList}
                      selectedValues={field.state.value}
                      onMultipleChange={(vals) =>
                        form.setFieldValue("statColumns", vals)
                      }
                      disabledValues={groupByColumnSet}
                      disabled={isSubmitting}
                      name="stat-columns"
                      error={tErr(
                        field.state.meta.errors,
                        "GroupStatistics.ErrorStatColumnsRequired",
                      )}
                      className="min-h-0 flex-1"
                    />
                  )}
                </form.Field>
              )}
            </div>

            {/* 右: 統計量 + 出力データ名 */}
            <div className="flex w-60 shrink-0 flex-col gap-3">
              {/* 統計量選択 */}
              <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <div className="mb-2 flex shrink-0 items-center justify-between">
                  <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                    {t("GroupStatistics.StatisticsLabel")}
                  </h2>
                  <SelectAllBar
                    selectAllLabel={t("GroupStatistics.SelectAll")}
                    deselectAllLabel={t("GroupStatistics.DeselectAll")}
                    onSelectAll={() =>
                      form.setFieldValue(
                        "statistics",
                        ALL_STAT_TYPES as DescriptiveStatisticType[],
                      )
                    }
                    onDeselectAll={() => form.setFieldValue("statistics", [])}
                    disabled={isSubmitting}
                  />
                </div>
                <div className="app-scrollbar min-h-0 flex-1 overflow-y-auto">
                  <form.Field name="statistics">
                    {(field) => (
                      <CheckboxTagGroup
                        items={ALL_STAT_TYPES.map((stat) => ({
                          value: stat,
                          label: t(`DescriptiveStatistics.Stat_${stat}`),
                        }))}
                        checked={checkedStats}
                        onToggle={(v) =>
                          toggleStat(v as DescriptiveStatisticType)
                        }
                        disabled={isSubmitting}
                        columns={2}
                        error={tErr(
                          field.state.meta.errors,
                          "GroupStatistics.ErrorStatisticsRequired",
                        )}
                      />
                    )}
                  </form.Field>
                </div>
              </div>

              {/* 出力データ名 */}
              <div className="shrink-0 rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <form.Field name="newTableName">
                  {(field) => (
                    <FormField
                      label={t("GroupStatistics.OutputDataLabel")}
                      htmlFor="group-statistics-new-table-name"
                      error={tErr(
                        field.state.meta.errors,
                        "GroupStatistics.ErrorOutputNameRequired",
                      )}
                    >
                      <InputText
                        id="group-statistics-new-table-name"
                        value={field.state.value}
                        onChange={(e) => field.handleChange(e.target.value)}
                        placeholder={t("GroupStatistics.OutputDataPlaceholder")}
                        disabled={isSubmitting}
                        data-testid="group-statistics-new-table-name"
                      />
                    </FormField>
                  )}
                </form.Field>
              </div>
            </div>
          </div>

          {/* ── BOTTOM: アクションバー ── */}
          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={
              isSubmitting
                ? t("GroupStatistics.Processing")
                : t("GroupStatistics.RunCalculation")
            }
            onCancel={handleCancel}
            onSelect={() => void form.handleSubmit()}
            disabled={isSubmitting}
            isLoading={isSubmitting}
          />
        </form>
      )}
    </PageLayout>
  );
};
