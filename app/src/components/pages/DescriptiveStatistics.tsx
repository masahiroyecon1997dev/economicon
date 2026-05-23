import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { DescriptiveStatisticsBody } from "@/api/zod/statistics/statistics";
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
  statistics: DescriptiveStatisticType[];
};

type DescriptiveStatisticsProps = {
  workTabId?: `work:DescriptiveStatistics`;
  onCancel?: () => void | Promise<void>;
};

const buildFormValues = (
  tableName: string,
  columnNames: string[],
  statistics: DescriptiveStatisticType[],
): DescriptiveStatisticsFormValues => ({
  tableName,
  columnNames,
  statistics,
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
  const closeActiveWorkTab = useWorkspaceTabsStore(
    (state) => state.closeActiveWorkTab,
  );
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

  const [checkedCols, setCheckedCols] = useState<Set<string>>(
    () => new Set(persistedDraft?.columnNames ?? []),
  );
  const [checkedStats, setCheckedStats] = useState<
    Set<DescriptiveStatisticType>
  >(() => new Set(persistedDraft?.statistics ?? DEFAULT_STAT_TYPES));
  const [isCalculating, setIsCalculating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [statsOpen, setStatsOpen] = useState(true);
  const [advancedStatsOpen, setAdvancedStatsOpen] = useState(false);

  const handleCancel = () => {
    if (onCancel) {
      void onCancel();
      return;
    }
    navigateToWorkspace();
  };

  const {
    selectedTableName: selectedTable,
    setSelectedTableName,
    columnList: columns,
    isLoading: isLoadingCols,
  } = useTableColumnLoader({
    initialSelectedTableName: persistedDraft?.tableName ?? initialTableName,
    onLoadedColumns: (loadedColumns) => {
      if (shouldAutoSelectColumnsRef.current) {
        setCheckedCols(new Set(loadedColumns.map((column) => column.name)));
        shouldAutoSelectColumnsRef.current = false;
        return;
      }

      const nextColumns = new Set(
        loadedColumns
          .map((column) => column.name)
          .filter((columnName) =>
            initialDraftRef.current?.columnNames.includes(columnName),
          ),
      );
      setCheckedCols(nextColumns);
    },
  });

  useEffect(() => {
    if (!workTabId || !selectedTable) {
      return;
    }

    const nextValues = buildFormValues(
      selectedTable,
      columns
        .map((column) => column.name)
        .filter((name) => checkedCols.has(name)),
      ALL_STAT_TYPES.filter((stat) => checkedStats.has(stat)),
    );
    ensureWorkTabState(workTabId, nextValues);
    updateWorkTabDraft(workTabId, nextValues);
  }, [
    checkedCols,
    checkedStats,
    columns,
    ensureWorkTabState,
    selectedTable,
    updateWorkTabDraft,
    workTabId,
  ]);

  const toggleCol = (name: string) => {
    setCheckedCols((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const toggleStat = (stat: DescriptiveStatisticType) => {
    setCheckedStats((prev) => {
      const next = new Set(prev);
      if (next.has(stat)) {
        next.delete(stat);
      } else {
        next.add(stat);
      }
      return next;
    });
  };

  const selectStats = (stats: DescriptiveStatisticType[]) => {
    setCheckedStats((prev) => {
      const next = new Set(prev);
      for (const stat of stats) {
        next.add(stat);
      }
      return next;
    });
  };

  const deselectStats = (stats: DescriptiveStatisticType[]) => {
    setCheckedStats((prev) => {
      const next = new Set(prev);
      for (const stat of stats) {
        next.delete(stat);
      }
      return next;
    });
  };

  const handleSubmit = async () => {
    const orderedCols = columns
      .map((column) => column.name)
      .filter((name) => checkedCols.has(name));
    const orderedStats = ALL_STAT_TYPES.filter((stat) =>
      checkedStats.has(stat),
    );

    const parsed = DescriptiveStatisticsBody.safeParse({
      tableName: selectedTable ?? "",
      columnNameList: orderedCols,
      statistics: orderedStats,
    });

    if (!parsed.success) {
      const firstPath = parsed.error.issues[0]?.path[0];
      let msg = t("Error.UnexpectedError");
      if (firstPath === "tableName")
        msg = t("DescriptiveStatistics.ErrorDataRequired");
      else if (firstPath === "columnNameList")
        msg = t("DescriptiveStatistics.ErrorColumnsRequired");
      else if (firstPath === "statistics")
        msg = t("DescriptiveStatistics.ErrorStatsRequired");
      setValidationError(msg);
      return;
    }
    setValidationError(null);

    setIsCalculating(true);
    try {
      const api = getEconomiconAppAPI();
      const response = await api.descriptiveStatistics({
        tableName: selectedTable,
        columnNameList: orderedCols,
        statistics: orderedStats,
      });

      if (response.code === "OK" && response.result) {
        const detailResponse = await api.getAnalysisResult(
          response.result.resultId,
        );
        if (detailResponse.code === "OK") {
          if (workTabId) {
            commitWorkTab(
              workTabId,
              buildFormValues(selectedTable, orderedCols, orderedStats),
            );
          }
          closeActiveWorkTab();
          openResultTab(detailResponse.result);
          await useAnalysisResultsStore.getState().fetchSummaries();
          return;
        }

        await showMessageDialog(
          t("Error.Error"),
          buildResponseErrorMessage(detailResponse, t("Error.UnexpectedError")),
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
    } finally {
      setIsCalculating(false);
    }
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
        <div className="app-scrollbar flex-1 min-h-0 space-y-4 overflow-y-auto pb-2">
          <FormField label={t("DescriptiveStatistics.DataLabel")}>
            <Select
              value={selectedTable}
              onValueChange={(value) => {
                setSelectedTableName(value);
                shouldAutoSelectColumnsRef.current = true;
                setCheckedCols(new Set());
                setValidationError(null);
              }}
              placeholder={t("DescriptiveStatistics.SelectData")}
            >
              {tableList.map((name) => (
                <SelectItem key={name} value={name}>
                  {name}
                </SelectItem>
              ))}
            </Select>
          </FormField>

          {selectedTable && (
            <FormField label={t("DescriptiveStatistics.ColumnsLabel")}>
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
                    deselectAllLabel={t("DescriptiveStatistics.DeselectAll")}
                    onSelectAll={() =>
                      setCheckedCols(
                        new Set(columns.map((column) => column.name)),
                      )
                    }
                    onDeselectAll={() => setCheckedCols(new Set())}
                  />
                  <CheckboxTagGroup
                    items={columns.map((column) => ({
                      value: column.name,
                      label: column.name,
                    }))}
                    checked={checkedCols}
                    onToggle={toggleCol}
                  />
                </div>
              )}
            </FormField>
          )}

          <div className="space-y-1">
            <button
              type="button"
              onClick={() => setStatsOpen((prev) => !prev)}
              className="flex w-full items-center justify-between py-0.5 text-sm font-medium text-gray-700 transition-colors hover:text-brand-accent dark:text-gray-300"
            >
              <span>{t("DescriptiveStatistics.StatisticsLabel")}</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-brand-text-main/60 transition-transform duration-200",
                  statsOpen && "rotate-180",
                )}
              />
            </button>
            {statsOpen && (
              <div className="space-y-2">
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-brand-text-main dark:text-gray-100">
                      {t("DescriptiveStatistics.PrimaryStatisticsLabel")}
                    </p>
                    <SelectAllBar
                      selectAllLabel={t("DescriptiveStatistics.SelectAll")}
                      deselectAllLabel={t("DescriptiveStatistics.DeselectAll")}
                      onSelectAll={() => selectStats(PRIMARY_STAT_TYPES)}
                      onDeselectAll={() => deselectStats(PRIMARY_STAT_TYPES)}
                    />
                  </div>
                  <CheckboxTagGroup
                    items={PRIMARY_STAT_TYPES.map((stat) => ({
                      value: stat,
                      label: t(`DescriptiveStatistics.Stat_${stat}`),
                    }))}
                    checked={checkedStats as Set<string>}
                    onToggle={(value) =>
                      toggleStat(value as DescriptiveStatisticType)
                    }
                    columns={3}
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
                        selectAllLabel={t("DescriptiveStatistics.SelectAll")}
                        deselectAllLabel={t(
                          "DescriptiveStatistics.DeselectAll",
                        )}
                        onSelectAll={() => selectStats(ADVANCED_STAT_TYPES)}
                        onDeselectAll={() => deselectStats(ADVANCED_STAT_TYPES)}
                      />
                      <CheckboxTagGroup
                        items={ADVANCED_STAT_TYPES.map((stat) => ({
                          value: stat,
                          label: t(`DescriptiveStatistics.Stat_${stat}`),
                        }))}
                        checked={checkedStats as Set<string>}
                        onToggle={(value) =>
                          toggleStat(value as DescriptiveStatisticType)
                        }
                        columns={3}
                      />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          {validationError && (
            <p className="text-xs text-red-600 dark:text-red-400">
              {validationError}
            </p>
          )}
          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={
              isCalculating
                ? t("DescriptiveStatistics.Processing")
                : t("DescriptiveStatistics.RunCalculation")
            }
            onCancel={handleCancel}
            onSelect={handleSubmit}
            disabled={isCalculating}
            isLoading={isCalculating}
          />
        </div>
      )}
    </PageLayout>
  );
};
