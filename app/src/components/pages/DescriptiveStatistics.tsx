import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
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
import { extractFieldError } from "@/lib/utils/formHelpers";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentPage";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { WorkspaceWorkTab } from "@/stores/workspaceTabs";
import {
  selectWorkTabDraft,
  useWorkspaceTabsStore,
} from "@/stores/workspaceTabs";
import { useForm, useStore } from "@tanstack/react-form";
import { ChevronDown, Loader2, SearchX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const descriptiveStatisticsDraftSchema = z.object({
  tableName: z.string(),
  columnNames: z.array(z.string()),
  statistics: z.array(z.string()),
});

const DEFAULT_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
];

const PRIMARY_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
];

const ADVANCED_STAT_TYPES: DescriptiveStatisticType[] = ALL_STAT_TYPES.filter(
  (stat) => !PRIMARY_STAT_TYPES.includes(stat),
);

type DescriptiveStatisticsFormValues = {
  tableName: string;
  columnNames: string[];
  statistics: string[];
};

type DescriptiveStatisticsProps = {
  workTabId?: `work:DescriptiveStatistics`;
  onCancel?: () => void | Promise<void>;
};

const createSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("DescriptiveStatistics.ErrorDataRequired")),
    columnNames: z
      .array(z.string())
      .min(1, t("DescriptiveStatistics.ErrorColumnsRequired")),
    statistics: z
      .array(z.string())
      .min(1, t("DescriptiveStatistics.ErrorStatsRequired")),
  });

export const DescriptiveStatistics = ({
  workTabId,
  onCancel,
}: DescriptiveStatisticsProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const initialTableName =
    useTableInfosStore((state) => state.activeTableName) ?? "";
  const navigateToShell = useCurrentPageStore((state) => state.navigateToShell);
  const navigateToWorkspace = useCurrentPageStore(
    (state) => state.navigateToWorkspace,
  );
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);
  const ensureWorkTabState = useWorkspaceTabsStore(
    (state) => state.ensureWorkTabState,
  );
  const updateWorkTabDraft = useWorkspaceTabsStore(
    (state) => state.updateWorkTabDraft,
  );
  const commitWorkTab = useWorkspaceTabsStore((state) => state.commitWorkTab);
  const persistedWorkTab = useWorkspaceTabsStore((state) =>
    workTabId
      ? (state.tabs.find(
          (
            tab,
          ): tab is WorkspaceWorkTab & {
            featureKey: "DescriptiveStatistics";
            id: `work:DescriptiveStatistics`;
          } =>
            tab.id === workTabId &&
            tab.kind === "work" &&
            tab.featureKey === "DescriptiveStatistics",
        ) ?? null)
      : null,
  );
  const persistedDraft = selectWorkTabDraft(
    persistedWorkTab,
    descriptiveStatisticsDraftSchema,
  ) as DescriptiveStatisticsFormValues | undefined;
  const initialDraftRef = useRef(persistedDraft);
  const shouldAutoSelectColumnsRef = useRef(
    !persistedDraft || persistedDraft.columnNames.length === 0,
  );
  const [advancedStatsOpen, setAdvancedStatsOpen] = useState(false);

  const handleCancel = () => {
    if (onCancel) {
      void onCancel();
      return;
    }
    navigateToWorkspace();
  };

  const form = useForm({
    defaultValues: {
      tableName: persistedDraft?.tableName ?? initialTableName,
      columnNames: persistedDraft?.columnNames ?? [],
      statistics: persistedDraft?.statistics ?? DEFAULT_STAT_TYPES,
    } satisfies DescriptiveStatisticsFormValues,
    validators: {
      onSubmit: createSchema(t),
    },
    onSubmit: async ({ value }) => {
      const orderedCols = columns
        .map((column) => column.name)
        .filter((name) => value.columnNames.includes(name));
      const orderedStats = ALL_STAT_TYPES.filter((stat) =>
        value.statistics.includes(stat),
      );

      try {
        const api = getEconomiconAppAPI();
        const response = await api.descriptiveStatistics({
          tableName: value.tableName,
          columnNameList: orderedCols,
          statistics: orderedStats,
        });

        if (response.code === "OK" && response.result) {
          const detailResponse = await api.getAnalysisResult(
            response.result.resultId,
          );
          if (detailResponse.code === "OK") {
            if (workTabId) {
              commitWorkTab(workTabId, {
                tableName: value.tableName,
                columnNames: orderedCols,
                statistics: orderedStats,
              });
            }
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
  const formValues = useStore(form.store, (s) => s.values);

  const {
    selectedTableName: selectedTable,
    setSelectedTableName,
    columnList: columns,
    isLoading: isLoadingCols,
  } = useTableColumnLoader({
    initialSelectedTableName: persistedDraft?.tableName ?? initialTableName,
    onLoadedColumns: (loadedColumns) => {
      if (shouldAutoSelectColumnsRef.current) {
        form.setFieldValue(
          "columnNames",
          loadedColumns.map((column) => column.name),
        );
        shouldAutoSelectColumnsRef.current = false;
        return;
      }

      form.setFieldValue(
        "columnNames",
        loadedColumns
          .map((column) => column.name)
          .filter((columnName) =>
            initialDraftRef.current?.columnNames.includes(columnName),
          ),
      );
    },
  });

  useEffect(() => {
    if (!workTabId) return;
    ensureWorkTabState(workTabId, formValues);
  }, [ensureWorkTabState, formValues, workTabId]);

  useEffect(() => {
    if (!workTabId) return;
    updateWorkTabDraft(workTabId, formValues);
  }, [formValues, updateWorkTabDraft, workTabId]);

  const checkedCols = new Set(formValues.columnNames);
  const checkedStats = new Set(formValues.statistics);

  const toggleStat = (stat: string) => {
    const next = new Set(checkedStats);
    if (next.has(stat)) next.delete(stat);
    else next.add(stat);
    form.setFieldValue("statistics", [...next]);
  };

  const selectStats = (stats: DescriptiveStatisticType[]) => {
    const next = new Set(checkedStats);
    for (const stat of stats) next.add(stat);
    form.setFieldValue("statistics", [...next]);
  };

  const deselectStats = (stats: DescriptiveStatisticType[]) => {
    const next = new Set(checkedStats);
    for (const stat of stats) next.delete(stat);
    form.setFieldValue("statistics", [...next]);
  };

  return (
    <PageLayout
      title={t("DescriptiveStatistics.Title")}
      description={t("DescriptiveStatistics.Description")}
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          className="flex-1"
          onCancel={handleCancel}
          onSelect={() => navigateToShell("ImportDataFile")}
        />
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            void form.handleSubmit();
          }}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="app-scrollbar flex-1 min-h-0 space-y-4 overflow-y-auto pb-2">
            <form.Field name="tableName">
              {(field) => (
                <FormField
                  label={t("DescriptiveStatistics.DataLabel")}
                  error={extractFieldError(field.state.meta.errors)}
                >
                  <Select
                    value={field.state.value}
                    onValueChange={(value) => {
                      field.handleChange(value);
                      setSelectedTableName(value);
                      shouldAutoSelectColumnsRef.current = true;
                      form.setFieldValue("columnNames", []);
                    }}
                    placeholder={t("DescriptiveStatistics.SelectData")}
                    disabled={isSubmitting}
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

            {selectedTable && (
              <form.Field name="columnNames">
                {(field) => (
                  <FormField
                    label={t("DescriptiveStatistics.ColumnsLabel")}
                    error={extractFieldError(field.state.meta.errors)}
                  >
                    {isLoadingCols ? (
                      <AnalysisEmptyState
                        compact
                        testId="descriptive-statistics-loading-columns-state"
                        icon={<Loader2 className="h-6 w-6 animate-spin" />}
                        title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                        description={t(
                          "AnalysisEmptyState.LoadingColumnsDescription",
                        )}
                      />
                    ) : columns.length === 0 ? (
                      <AnalysisEmptyState
                        compact
                        testId="descriptive-statistics-no-columns-state"
                        icon={<SearchX className="h-6 w-6" />}
                        title={t("AnalysisEmptyState.NoEligibleColumnsTitle")}
                        description={t("DescriptiveStatistics.NoColumns")}
                        hint={t("AnalysisEmptyState.NoEligibleColumnsHint")}
                      />
                    ) : (
                      <div className="space-y-2">
                        <SelectAllBar
                          selectAllLabel={t("DescriptiveStatistics.SelectAll")}
                          deselectAllLabel={t(
                            "DescriptiveStatistics.DeselectAll",
                          )}
                          onSelectAll={() =>
                            form.setFieldValue(
                              "columnNames",
                              columns.map((column) => column.name),
                            )
                          }
                          onDeselectAll={() =>
                            form.setFieldValue("columnNames", [])
                          }
                          disabled={isSubmitting}
                        />
                        <CheckboxTagGroup
                          items={columns.map((column) => ({
                            value: column.name,
                            label: column.name,
                          }))}
                          checked={checkedCols}
                          onToggle={(name) => {
                            const next = new Set(checkedCols);
                            if (next.has(name)) next.delete(name);
                            else next.add(name);
                            field.handleChange([...next]);
                          }}
                          disabled={isSubmitting}
                        />
                      </div>
                    )}
                  </FormField>
                )}
              </form.Field>
            )}

            <div className="space-y-1">
              <form.Field name="statistics">
                {(field) => (
                  <div className="space-y-2">
                    {extractFieldError(field.state.meta.errors) && (
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {extractFieldError(field.state.meta.errors)}
                      </p>
                    )}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-brand-text-main dark:text-gray-100">
                          {t("DescriptiveStatistics.PrimaryStatisticsLabel")}
                        </p>
                        <SelectAllBar
                          selectAllLabel={t("DescriptiveStatistics.SelectAll")}
                          deselectAllLabel={t(
                            "DescriptiveStatistics.DeselectAll",
                          )}
                          onSelectAll={() => selectStats(PRIMARY_STAT_TYPES)}
                          onDeselectAll={() =>
                            deselectStats(PRIMARY_STAT_TYPES)
                          }
                          disabled={isSubmitting}
                        />
                      </div>
                      <CheckboxTagGroup
                        items={PRIMARY_STAT_TYPES.map((stat) => ({
                          value: stat,
                          label: t(`DescriptiveStatistics.Stat_${stat}`),
                        }))}
                        checked={checkedStats}
                        onToggle={toggleStat}
                        columns={3}
                        disabled={isSubmitting}
                      />
                    </div>

                    <div className="space-y-2 rounded-lg border border-border-color/70 bg-white/70 p-3 dark:border-gray-700 dark:bg-gray-800/40">
                      <button
                        type="button"
                        onClick={() => setAdvancedStatsOpen((prev) => !prev)}
                        className="flex w-full items-center justify-between text-left text-sm font-medium text-gray-700 transition-colors hover:text-brand-accent dark:text-gray-300"
                      >
                        <span>
                          {t("DescriptiveStatistics.AdvancedStatisticsLabel")}
                        </span>
                        <ChevronDown
                          className={cn(
                            "h-4 w-4 text-brand-text-main/60 transition-transform duration-200",
                            advancedStatsOpen && "rotate-180",
                          )}
                        />
                      </button>

                      {advancedStatsOpen && (
                        <div className="space-y-2">
                          <SelectAllBar
                            selectAllLabel={t(
                              "DescriptiveStatistics.SelectAll",
                            )}
                            deselectAllLabel={t(
                              "DescriptiveStatistics.DeselectAll",
                            )}
                            onSelectAll={() => selectStats(ADVANCED_STAT_TYPES)}
                            onDeselectAll={() =>
                              deselectStats(ADVANCED_STAT_TYPES)
                            }
                            disabled={isSubmitting}
                          />
                          <CheckboxTagGroup
                            items={ADVANCED_STAT_TYPES.map((stat) => ({
                              value: stat,
                              label: t(`DescriptiveStatistics.Stat_${stat}`),
                            }))}
                            checked={checkedStats}
                            onToggle={toggleStat}
                            columns={3}
                            disabled={isSubmitting}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </form.Field>
            </div>
          </div>

          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={
              isSubmitting
                ? t("DescriptiveStatistics.Processing")
                : t("DescriptiveStatistics.RunCalculation")
            }
            onCancel={handleCancel}
            onSelect={() => void form.handleSubmit()}
            onSelectType="submit"
            disabled={isSubmitting}
            isLoading={isSubmitting}
          />
        </form>
      )}
    </PageLayout>
  );
};
