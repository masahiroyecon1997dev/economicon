import { getEconomiconAppAPI } from "@/api/endpoints";
import { DescriptiveStatisticType } from "@/api/model";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { CheckboxTagGroup } from "@/components/molecules/Field/CheckboxTagGroup";
import { SelectAllBar } from "@/components/molecules/Field/SelectAllBar";
import { FormField } from "@/components/molecules/Form/FormField";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { WorkspaceWorkTab } from "@/stores/workspaceTabs";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

const ALL_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.mode,
  DescriptiveStatisticType.variance,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.range,
  DescriptiveStatisticType.iqr,
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
  DescriptiveStatisticType.population_variance,
];

type FormErrors = {
  table?: string;
  columns?: string;
  stats?: string;
};

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
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
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
  const persistedDraft = persistedWorkTab?.draftValues as
    | DescriptiveStatisticsFormValues
    | undefined;
  const initialDraftRef = useRef(persistedDraft);
  const shouldAutoSelectColumnsRef = useRef(
    !persistedDraft || persistedDraft.columnNames.length === 0,
  );

  const [checkedCols, setCheckedCols] = useState<Set<string>>(
    () => new Set(persistedDraft?.columnNames ?? []),
  );
  const [checkedStats, setCheckedStats] = useState<
    Set<DescriptiveStatisticType>
  >(() => new Set(persistedDraft?.statistics ?? ALL_STAT_TYPES));
  const [isCalculating, setIsCalculating] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [statsOpen, setStatsOpen] = useState(true);

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

  const handleSubmit = async () => {
    const newErrors: FormErrors = {};
    if (!selectedTable) {
      newErrors.table = t("DescriptiveStatistics.ErrorDataRequired");
    }
    if (checkedCols.size === 0) {
      newErrors.columns = t("DescriptiveStatistics.ErrorColumnsRequired");
    }
    if (checkedStats.size === 0) {
      newErrors.stats = t("DescriptiveStatistics.ErrorStatsRequired");
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});

    const orderedCols = columns
      .map((column) => column.name)
      .filter((name) => checkedCols.has(name));
    const orderedStats = ALL_STAT_TYPES.filter((stat) =>
      checkedStats.has(stat),
    );

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
          openResultTab(detailResponse.result);
          await useAnalysisResultsStore.getState().fetchSummaries();
          setCurrentView("DataPreview");
          return;
        }
      }

      await showMessageDialog(
        t("DescriptiveStatistics.ErrorCalculation"),
        "error",
      );
    } catch {
      await showMessageDialog(
        t("DescriptiveStatistics.ErrorCalculation"),
        "error",
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
      <div className="app-scrollbar flex-1 min-h-0 space-y-4 overflow-y-auto pb-2">
        <FormField
          label={t("DescriptiveStatistics.DataLabel")}
          error={errors.table}
        >
          <Select
            value={selectedTable}
            onValueChange={(value) => {
              setSelectedTableName(value);
              shouldAutoSelectColumnsRef.current = true;
              setCheckedCols(new Set());
              setErrors({});
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
              <p className="text-sm text-brand-text-sub">
                {t("DescriptiveStatistics.LoadingColumns")}
              </p>
            ) : columns.length === 0 ? (
              <p className="text-sm text-brand-text-sub">
                {t("DescriptiveStatistics.NoColumns")}
              </p>
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
                  error={errors.columns}
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
              <SelectAllBar
                selectAllLabel={t("DescriptiveStatistics.SelectAll")}
                deselectAllLabel={t("DescriptiveStatistics.DeselectAll")}
                onSelectAll={() => setCheckedStats(new Set(ALL_STAT_TYPES))}
                onDeselectAll={() => setCheckedStats(new Set())}
              />
              <CheckboxTagGroup
                items={ALL_STAT_TYPES.map((stat) => ({
                  value: stat,
                  label: t(`DescriptiveStatistics.Stat_${stat}`),
                }))}
                checked={checkedStats as Set<string>}
                onToggle={(value) =>
                  toggleStat(value as DescriptiveStatisticType)
                }
                error={errors.stats}
                columns={3}
              />
            </div>
          )}
          {!statsOpen && errors.stats && (
            <p className="mt-0.5 text-xs text-red-600 dark:text-red-400">
              {errors.stats}
            </p>
          )}
        </div>
      </div>
      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isCalculating
            ? t("DescriptiveStatistics.Processing")
            : t("DescriptiveStatistics.RunCalculation")
        }
        onCancel={() => {
          if (onCancel) {
            void onCancel();
            return;
          }
          setCurrentView("DataPreview");
        }}
        onSelect={handleSubmit}
        disabled={isCalculating}
        isLoading={isCalculating}
      />
    </PageLayout>
  );
};
