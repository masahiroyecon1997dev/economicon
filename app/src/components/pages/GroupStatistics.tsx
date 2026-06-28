import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { CreateGroupStatisticsTableBody } from "@/api/zod/statistics/statistics";
import { Button } from "@/components/atoms/Button/Button";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ExplainerButton } from "@/components/molecules/Dialog/ExplainerButton";
import { CheckboxTagGroup } from "@/components/molecules/Field/CheckboxTagGroup";
import { SelectAllBar } from "@/components/molecules/Field/SelectAllBar";
import { FormField } from "@/components/molecules/Form/FormField";
import {
  AnalysisEmptyState,
  AnalysisNoTablesState,
} from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { PageLayout } from "@/components/templates/PageLayout";
import { ALL_STAT_TYPES } from "@/constants/statisticTypes";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { createFieldError } from "@/lib/utils/formHelpers";
import { cn } from "@/lib/utils/helpers";
import { getTableInfo } from "@/lib/utils/internal";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { WorkspaceWorkTab } from "@/stores/workspaceTabs";
import {
  selectWorkTabDraft,
  useWorkspaceTabsStore,
} from "@/stores/workspaceTabs";
import type { ColumnType } from "@/types/commonTypes";
import { useForm, useStore } from "@tanstack/react-form";
import { ChevronDown, HelpCircle, Loader2, SearchX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

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

const SECONDARY_STAT_TYPES = ALL_STAT_TYPES.filter(
  (stat) => !DEFAULT_STAT_TYPES.includes(stat),
);

const isFloatColumn = (col: ColumnType): boolean =>
  col.type === "Float32" || col.type === "Float64";

const buildDefaultOutputName = (tableName: string): string =>
  tableName ? `${tableName}_group_statistics` : "";

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

export const GroupStatistics = ({
  workTabId,
  onSuccess,
  onCancel,
}: GroupStatisticsProps) => {
  const { t } = useTranslation();
  const errorParamMap = {
    newTableName: t("GroupStatistics.OutputDataLabel"),
  };
  const tableList = useTableListStore((s) => s.tableList);
  const addTableName = useTableListStore((s) => s.addTableName);
  const initialTableName = useTableInfosStore((s) => s.activeTableName) ?? "";
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);
  const navigateToShell = useCurrentPageStore((s) => s.navigateToShell);
  const navigateToWorkspace = useCurrentPageStore((s) => s.navigateToWorkspace);
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

  const persistedDraft = selectWorkTabDraft(
    persistedWorkTab,
    CreateGroupStatisticsTableBody,
  );
  const shouldAutoSelectRef = useRef(!persistedDraft);
  const [columnFilter, setColumnFilter] = useState("");
  const [showAllStats, setShowAllStats] = useState(false);

  const initialValues: GroupStatisticsFormValues = {
    tableName: persistedDraft?.tableName ?? initialTableName,
    groupByColumns: persistedDraft?.groupByColumns ?? [],
    statColumns: persistedDraft?.statColumns ?? [],
    statistics: persistedDraft?.statistics ?? DEFAULT_STAT_TYPES,
    newTableName:
      persistedDraft?.newTableName ?? buildDefaultOutputName(initialTableName),
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
            navigateToWorkspace();
          }
        } else {
          await showMessageDialog(
            t("Error.Error"),
            buildResponseErrorMessage(
              resp,
              t("Error.UnexpectedError"),
              errorParamMap,
            ),
          );
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          buildCaughtErrorMessage(
            error,
            t("Error.UnexpectedError"),
            errorParamMap,
          ),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  const isSubmitted = useStore(form.store, (s) => s.isSubmitted);
  const formValues = useStore(form.store, (s) => s.values);

  const groupByColumnSet = new Set(formValues.groupByColumns);
  const lowerColumnFilter = columnFilter.trim().toLowerCase();
  const filteredColumns = columnList.filter((column) =>
    column.name.toLowerCase().includes(lowerColumnFilter),
  );
  const checkedStats = new Set(formValues.statistics);

  useEffect(() => {
    if (!shouldAutoSelectRef.current || columnList.length === 0) return;
    shouldAutoSelectRef.current = false;
  }, [columnList]);

  useEffect(() => {
    if (!selectedTableName || formValues.newTableName.trim()) return;
    form.setFieldValue(
      "newTableName",
      buildDefaultOutputName(selectedTableName),
    );
  }, [form, formValues.newTableName, selectedTableName]);

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
    if (!value) {
      setColumnList([]);
    }
    shouldAutoSelectRef.current = !!value;
    form.setFieldValue("tableName", value);
    form.setFieldValue("groupByColumns", []);
    form.setFieldValue("statColumns", []);
    form.setFieldValue("newTableName", buildDefaultOutputName(value));
  };

  const handleGroupByChange = (newGroupBy: string[]) => {
    form.setFieldValue("groupByColumns", newGroupBy);
    const filteredStatCols = formValues.statColumns.filter(
      (column) => !newGroupBy.includes(column),
    );
    form.setFieldValue("statColumns", filteredStatCols);
  };

  const toggleGroupRole = (columnName: string) => {
    const targetColumn = columnList.find(
      (column) => column.name === columnName,
    );
    if (!targetColumn || isFloatColumn(targetColumn)) return;

    if (groupByColumnSet.has(columnName)) {
      handleGroupByChange(
        formValues.groupByColumns.filter((value) => value !== columnName),
      );
      return;
    }

    handleGroupByChange([...formValues.groupByColumns, columnName]);
  };

  const toggleStatRole = (columnName: string) => {
    if (groupByColumnSet.has(columnName)) return;

    const nextValues = formValues.statColumns.includes(columnName)
      ? formValues.statColumns.filter((value) => value !== columnName)
      : [...formValues.statColumns, columnName];

    form.setFieldValue("statColumns", nextValues);
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
    navigateToWorkspace();
  };

  const tErr = createFieldError(t);
  const groupByError =
    isSubmitted && formValues.groupByColumns.length === 0
      ? t("GroupStatistics.ErrorGroupByRequired")
      : undefined;
  const statColumnsError =
    isSubmitted && formValues.statColumns.length === 0
      ? t("GroupStatistics.ErrorStatColumnsRequired")
      : undefined;
  const statisticsError =
    isSubmitted && formValues.statistics.length === 0
      ? t("GroupStatistics.ErrorStatisticsRequired")
      : undefined;
  const outputNameError =
    isSubmitted && !formValues.newTableName.trim()
      ? t("GroupStatistics.ErrorOutputNameRequired")
      : undefined;

  return (
    <PageLayout
      title={t("GroupStatistics.Title")}
      description={t("GroupStatistics.Description")}
      titleAction={
        <ExplainerButton
          explainerKey="group_statistics"
          aria-label={t("GroupStatistics.ExplainerButtonLabel")}
          data-testid="group-statistics-explainer-btn"
        >
          <HelpCircle className="h-4 w-4" aria-hidden="true" />
        </ExplainerButton>
      }
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          className="flex-1"
          onCancel={handleCancel}
          onSelect={() => navigateToShell("ImportDataFile")}
        />
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            event.stopPropagation();
            void form.handleSubmit();
          }}
          className="flex min-h-0 flex-1 flex-col gap-2"
        >
          {/* 上段: 対象データ + 出力データ名 */}
          <div className="grid shrink-0 grid-cols-2 gap-2">
            <form.Field name="tableName">
              {(field) => (
                <FormField
                  label={t("GroupStatistics.DataLabel")}
                  htmlFor="group-statistics-table-name"
                  error={tErr(
                    field.state.meta.errors,
                    "GroupStatistics.ErrorDataRequired",
                  )}
                >
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
                </FormField>
              )}
            </form.Field>

            <FormField
              label={t("GroupStatistics.OutputDataLabel")}
              htmlFor="group-statistics-new-table-name"
              error={outputNameError}
            >
              <InputText
                id="group-statistics-new-table-name"
                value={formValues.newTableName}
                onChange={(event) =>
                  form.setFieldValue("newTableName", event.target.value)
                }
                placeholder={t("GroupStatistics.OutputDataPlaceholder")}
                disabled={isSubmitting}
                data-testid="group-statistics-new-table-name"
              />
            </FormField>
          </div>

          {/* 中段: 列マトリクス + 統計量 */}
          <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_240px] gap-2">
            {/* 列マトリクス */}
            <div
              className="flex min-h-0 flex-col rounded-xl border border-border-color bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
              data-testid="group-statistics-role-matrix"
            >
              <div className="flex items-center justify-between gap-2 border-b border-border-color px-3 py-2">
                <span className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-sub">
                  {t("GroupStatistics.ColumnSearchLabel")}
                </span>
                <div className="w-48">
                  <label
                    htmlFor="group-statistics-column-filter"
                    className="sr-only"
                  >
                    {t("GroupStatistics.ColumnSearchLabel")}
                  </label>
                  <InputText
                    id="group-statistics-column-filter"
                    value={columnFilter}
                    onChange={(event) => setColumnFilter(event.target.value)}
                    placeholder={t("Common.FilterColumns")}
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="grid grid-cols-[minmax(0,1fr)_110px_110px] gap-2 border-b border-border-color px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-sub">
                <span>{t("GroupStatistics.ColumnLabel")}</span>
                <span>{t("GroupStatistics.GroupByColumnsLabel")}</span>
                <span>{t("GroupStatistics.StatColumnsLabel")}</span>
              </div>

              {!selectedTableName ? (
                <div className="p-3 text-sm text-brand-text-sub">
                  {t("GroupStatistics.SelectData")}
                </div>
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
              ) : filteredColumns.length === 0 ? (
                <AnalysisEmptyState
                  compact
                  testId="group-statistics-no-filter-columns"
                  icon={<SearchX className="h-6 w-6" />}
                  title={t("GroupStatistics.NoMatchingColumnsTitle")}
                  description={t(
                    "GroupStatistics.NoMatchingColumnsDescription",
                  )}
                  className="flex-1"
                />
              ) : (
                <div className="app-scrollbar min-h-0 flex-1 overflow-y-auto">
                  {filteredColumns.map((column) => {
                    const isGroupColumn = formValues.groupByColumns.includes(
                      column.name,
                    );
                    const isStatColumn = formValues.statColumns.includes(
                      column.name,
                    );
                    const isGroupDisabled = isFloatColumn(column);
                    const isStatDisabled = isGroupColumn;

                    return (
                      <div
                        key={column.name}
                        className="grid grid-cols-[minmax(0,1fr)_110px_110px] items-center gap-2 border-b border-border-color/80 px-3 py-1.5 last:border-b-0"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <p className="truncate text-xs font-medium text-text-heading dark:text-gray-100">
                              {column.name}
                            </p>
                            <span className="rounded-full bg-secondary px-1.5 py-0.5 text-[10px] text-brand-text-sub">
                              {column.type}
                            </span>
                          </div>
                        </div>

                        <Button
                          variant={isGroupColumn ? "primary" : "outline"}
                          className="px-2 py-1 text-xs"
                          onClick={() => toggleGroupRole(column.name)}
                          disabled={isSubmitting || isGroupDisabled}
                        >
                          {isGroupColumn
                            ? t("GroupStatistics.RoleSelected")
                            : t("GroupStatistics.AssignGroupRole")}
                        </Button>

                        <Button
                          variant={isStatColumn ? "primary" : "outline"}
                          className="px-2 py-1 text-xs"
                          onClick={() => toggleStatRole(column.name)}
                          disabled={isSubmitting || isStatDisabled}
                        >
                          {isStatColumn
                            ? t("GroupStatistics.RoleSelected")
                            : t("GroupStatistics.AssignStatRole")}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 統計量 */}
            <div className="flex min-h-0 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="mb-2 flex shrink-0 items-center justify-between gap-1">
                <span className="text-xs font-semibold uppercase tracking-[0.14em] text-brand-text-sub">
                  {t("GroupStatistics.StatisticsLabel")}
                </span>
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
                <CheckboxTagGroup
                  items={DEFAULT_STAT_TYPES.map((stat) => ({
                    value: stat,
                    label: t(`DescriptiveStatistics.Stat_${stat}`),
                  }))}
                  checked={checkedStats}
                  onToggle={(value) =>
                    toggleStat(value as DescriptiveStatisticType)
                  }
                  disabled={isSubmitting}
                  columns={1}
                  compact
                  error={statisticsError}
                />
                <button
                  type="button"
                  onClick={() => setShowAllStats((v) => !v)}
                  className="mt-2 flex w-full items-center gap-1 rounded py-1 text-[11px] text-brand-text-sub hover:text-brand-text-main"
                  disabled={isSubmitting}
                >
                  <ChevronDown
                    className={cn(
                      "h-3 w-3 shrink-0 transition-transform",
                      showAllStats && "rotate-180",
                    )}
                  />
                  {showAllStats
                    ? t("GroupStatistics.HideAdvancedStats")
                    : t("GroupStatistics.ShowAdvancedStats")}
                </button>
                {showAllStats && (
                  <div className="mt-1">
                    <CheckboxTagGroup
                      items={SECONDARY_STAT_TYPES.map((stat) => ({
                        value: stat,
                        label: t(`DescriptiveStatistics.Stat_${stat}`),
                      }))}
                      checked={checkedStats}
                      onToggle={(value) =>
                        toggleStat(value as DescriptiveStatisticType)
                      }
                      disabled={isSubmitting}
                      columns={1}
                      compact
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {(groupByError || statColumnsError) && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {groupByError ?? statColumnsError}
            </div>
          )}

          <div className="flex shrink-0 justify-end gap-2 border-t border-border-color py-2 dark:border-gray-700">
            <Button
              onClick={handleCancel}
              variant="outline"
              className="px-4 py-1.5"
              disabled={isSubmitting}
            >
              {t("Common.Cancel")}
            </Button>
            <Button
              onClick={() => void form.handleSubmit()}
              variant="primary"
              className="inline-flex items-center gap-1 px-4 py-1.5"
              disabled={isSubmitting}
            >
              {isSubmitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {isSubmitting
                ? t("GroupStatistics.Processing")
                : t("GroupStatistics.RunCalculation")}
            </Button>
          </div>
        </form>
      )}
    </PageLayout>
  );
};
