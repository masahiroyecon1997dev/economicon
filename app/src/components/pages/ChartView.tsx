import { fetchPlotDataBinary } from "@/api/bridge/tauri-commands";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { VariableSelectorField } from "@/components/molecules/Field/VariableSelectorField";
import {
  AnalysisEmptyState,
  AnalysisNoTablesState,
} from "@/components/organisms/EmptyState/AnalysisNoTablesState";
import { PageLayout } from "@/components/templates/PageLayout";
import { useTableColumnLoader } from "@/hooks/useTableColumnLoader";
import { showMessageDialog } from "@/lib/dialog/message";
import { buildCaughtErrorMessage } from "@/lib/utils/apiError";
import { cn } from "@/lib/utils/helpers";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import type { ColumnType } from "@/types/commonTypes";
import { tableFromIPC, type Table as ArrowTable } from "apache-arrow";
import { BarChart2, Loader2 } from "lucide-react";
import type { Config, Data, Datum, Layout } from "plotly.js";
import * as Plotly from "plotly.js-dist-min";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

// ---------------------------------------------------------------------------
// Constants & helpers
// ---------------------------------------------------------------------------

type ChartType = "scatter" | "histogram" | "line";

const NUMERIC_TYPES = new Set([
  "Float32",
  "Float64",
  "Int8",
  "Int16",
  "Int32",
  "Int64",
  "UInt8",
  "UInt16",
  "UInt32",
  "UInt64",
]);

const isNumericColumn = (col: ColumnType): boolean =>
  NUMERIC_TYPES.has(col.type);

const getColNumbers = (
  arrowTable: ArrowTable,
  colName: string,
): (number | null)[] => {
  const col = arrowTable.getChild(colName);
  if (!col) return [];
  const result: (number | null)[] = [];
  for (let i = 0; i < col.length; i++) {
    const val = col.get(i);
    result.push(val === null || val === undefined ? null : Number(val));
  }
  return result;
};

const getColValues = (arrowTable: ArrowTable, colName: string): Datum[] => {
  const col = arrowTable.getChild(colName);
  if (!col) return [];
  const result: Datum[] = [];
  for (let i = 0; i < col.length; i++) {
    const val = col.get(i);
    if (val === null || val === undefined) {
      result.push(null);
    } else if (typeof val === "boolean") {
      result.push(val ? 1 : 0);
    } else {
      result.push(val as Datum);
    }
  }
  return result;
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ChartViewProps = {
  workTabId?: `work:ChartView`;
  onCancel?: () => void | Promise<void>;
};

const CHART_TYPE_KEYS: { type: ChartType; labelKey: string }[] = [
  { type: "scatter", labelKey: "ChartView.ChartTypeScatter" },
  { type: "histogram", labelKey: "ChartView.ChartTypeHistogram" },
  { type: "line", labelKey: "ChartView.ChartTypeLine" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const ChartView = ({
  workTabId: _workTabId,
  onCancel,
}: ChartViewProps) => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const initialTableName = useTableInfosStore((s) => s.activeTableName) ?? "";
  const navigateToShell = useCurrentPageStore((s) => s.navigateToShell);
  const navigateToWorkspace = useCurrentPageStore((s) => s.navigateToWorkspace);

  // Form state (no submission — pure visualization)
  const [tableName, setTableName] = useState(initialTableName);
  const [chartType, setChartType] = useState<ChartType>("scatter");
  const [xColumn, setXColumn] = useState("");
  const [yColumn, setYColumn] = useState(""); // scatter only
  const [yColumns, setYColumns] = useState<string[]>([]); // line only

  // Chart render state
  const [isRendering, setIsRendering] = useState(false);
  const [hasChartData, setHasChartData] = useState(false);

  const plotDivRef = useRef<HTMLDivElement>(null);

  const {
    selectedTableName,
    setSelectedTableName,
    columnList,
    setColumnList,
    isLoading,
  } = useTableColumnLoader({
    numericOnly: false,
    autoLoadOnMount: !!initialTableName,
    initialSelectedTableName: initialTableName,
  });

  const numericColumns = columnList.filter(isNumericColumn);
  // X-axis: numeric for scatter/histogram, any for line
  const xAxisColumns = chartType === "line" ? columnList : numericColumns;
  const yAxisColumns = numericColumns;

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  const clearChart = () => {
    setHasChartData(false);
    if (plotDivRef.current) {
      Plotly.purge(plotDivRef.current);
    }
  };

  const handleTableChange = (value: string) => {
    setTableName(value);
    setSelectedTableName(value);
    if (!value) setColumnList([]);
    setXColumn("");
    setYColumn("");
    setYColumns([]);
    clearChart();
  };

  const handleChartTypeChange = (type: ChartType) => {
    setChartType(type);
    setYColumn("");
    setYColumns([]);
    clearChart();
  };

  const handleCancel = () => {
    if (onCancel) {
      void onCancel();
      return;
    }
    navigateToWorkspace();
  };

  // ---------------------------------------------------------------------------
  // Debounced fetch & render (400 ms)
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const isReady =
      !!tableName &&
      !!xColumn &&
      (chartType === "scatter"
        ? !!yColumn
        : chartType === "histogram"
          ? true
          : yColumns.length > 0);

    if (!isReady) return;

    const requiredColumns =
      chartType === "scatter"
        ? [xColumn, yColumn]
        : chartType === "histogram"
          ? [xColumn]
          : [xColumn, ...yColumns];

    const timer = setTimeout(() => {
      const renderChart = async () => {
        if (!plotDivRef.current) return;
        setIsRendering(true);
        try {
          const bytes = await fetchPlotDataBinary(tableName, requiredColumns);
          const arrowTable = tableFromIPC(bytes) as ArrowTable;

          let traces: Data[];

          if (chartType === "scatter") {
            traces = [
              {
                type: "scatter",
                mode: "markers",
                x: getColNumbers(arrowTable, xColumn),
                y: getColNumbers(arrowTable, yColumn),
                name: yColumn,
                marker: { opacity: 0.65, size: 6 },
              },
            ];
          } else if (chartType === "histogram") {
            traces = [
              {
                type: "histogram",
                x: getColNumbers(arrowTable, xColumn),
                name: xColumn,
              },
            ];
          } else {
            const xData = getColValues(arrowTable, xColumn);
            traces = yColumns.map((yCol) => ({
              type: "scatter" as const,
              mode: "lines" as const,
              x: xData,
              y: getColNumbers(arrowTable, yCol),
              name: yCol,
            }));
          }

          const layout: Partial<Layout> = {
            autosize: true,
            margin: { l: 60, r: 24, t: 30, b: 60 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(248,250,252,1)",
            xaxis: {
              title: { text: xColumn },
              gridcolor: "rgba(156,163,175,0.3)",
              linecolor: "rgba(156,163,175,0.5)",
              zerolinecolor: "rgba(156,163,175,0.3)",
            },
            yaxis: {
              title: {
                text: chartType === "line" ? "" : yColumn,
              },
              gridcolor: "rgba(156,163,175,0.3)",
              linecolor: "rgba(156,163,175,0.5)",
              zerolinecolor: "rgba(156,163,175,0.3)",
            },
            font: { size: 12, color: "#374151" },
            showlegend: chartType === "line",
            legend: { orientation: "h", y: -0.2 },
          };

          const config: Partial<Config> = {
            responsive: true,
            displayModeBar: false,
          };

          if (plotDivRef.current) {
            await Plotly.react(plotDivRef.current, traces, layout, config);
            setHasChartData(true);
          }
        } catch (error) {
          await showMessageDialog(
            t("Error.Error"),
            buildCaughtErrorMessage(error, t("Error.UnexpectedError")),
          );
        } finally {
          setIsRendering(false);
        }
      };

      void renderChart();
    }, 400);

    return () => clearTimeout(timer);
  }, [tableName, chartType, xColumn, yColumn, yColumns, t]);

  // Cleanup Plotly on unmount
  useEffect(() => {
    const div = plotDivRef.current;
    return () => {
      if (div) {
        Plotly.purge(div);
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const emptyHint = (() => {
    if (!tableName)
      return {
        title: t("ChartView.EmptyNeedTable"),
        description: t("ChartView.EmptyNeedTableDesc"),
      };
    if (!xColumn)
      return {
        title: t("ChartView.EmptyNeedXColumn"),
        description: t("ChartView.EmptyNeedXColumnDesc"),
      };
    if (chartType === "scatter" && !yColumn)
      return {
        title: t("ChartView.EmptyNeedYColumn"),
        description: t("ChartView.EmptyNeedYColumnDesc"),
      };
    if (chartType === "line" && yColumns.length === 0)
      return {
        title: t("ChartView.EmptyNeedYColumns"),
        description: t("ChartView.EmptyNeedYColumnsDesc"),
      };
    return {
      title: t("ChartView.EmptyTitle"),
      description: t("ChartView.EmptyDescription"),
    };
  })();

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <PageLayout
      title={t("ChartView.Title")}
      description={t("ChartView.Description")}
    >
      {tableList.length === 0 ? (
        <AnalysisNoTablesState
          className="flex-1"
          onCancel={handleCancel}
          onSelect={() => navigateToShell("ImportDataFile")}
        />
      ) : (
        <div className="flex min-h-0 flex-1 gap-3">
          {/* ── Left: Settings Panel ── */}
          <div className="flex w-72 shrink-0 flex-col gap-3 overflow-y-auto">
            {/* Data selector */}
            <div className="rounded-xl border border-border-color bg-white px-3 py-2 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center gap-3">
                <label className="shrink-0 text-xs font-medium text-brand-text-main">
                  {t("ChartView.DataLabel")}
                </label>
                <div className="flex-1">
                  <Select
                    value={tableName}
                    onValueChange={handleTableChange}
                    placeholder={t("ChartView.SelectData")}
                    data-testid="chart-view-table-select"
                  >
                    {tableList.map((name) => (
                      <SelectItem key={name} value={name}>
                        {name}
                      </SelectItem>
                    ))}
                  </Select>
                </div>
              </div>
            </div>

            {/* Chart type selector */}
            <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
              <h2 className="text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                {t("ChartView.ChartTypeLabel")}
              </h2>
              <div className="mt-2 flex gap-1">
                {CHART_TYPE_KEYS.map(({ type, labelKey }) => (
                  <button
                    key={type}
                    type="button"
                    data-testid={`chart-type-${type}`}
                    onClick={() => handleChartTypeChange(type)}
                    className={cn(
                      "flex flex-1 items-center justify-center rounded-lg border px-2 py-1.5 text-xs font-medium transition-colors",
                      chartType === type
                        ? "border-brand-primary bg-brand-primary/10 text-brand-primary"
                        : "border-border-color text-brand-text-sub hover:border-brand-primary/40 hover:text-brand-text-main",
                    )}
                  >
                    {t(labelKey)}
                  </button>
                ))}
              </div>
            </div>

            {/* Column selectors (shown when table is selected) */}
            {selectedTableName && (
              <div className="flex flex-1 flex-col rounded-xl border border-border-color bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
                <h2 className="mb-2 shrink-0 text-sm font-bold leading-tight text-text-heading dark:text-gray-100">
                  {t("ChartView.ColumnsLabel")}
                </h2>

                {isLoading ? (
                  <AnalysisEmptyState
                    compact
                    testId="chart-view-loading-columns"
                    icon={<Loader2 className="h-6 w-6 animate-spin" />}
                    title={t("AnalysisEmptyState.LoadingColumnsTitle")}
                    description={t(
                      "AnalysisEmptyState.LoadingColumnsDescription",
                    )}
                  />
                ) : (
                  <div className="flex flex-col gap-3">
                    {/* X axis */}
                    <div>
                      <label className="mb-1 block text-xs font-medium text-brand-text-main">
                        {t("ChartView.XColumnLabel")}
                      </label>
                      <Select
                        value={xColumn}
                        onValueChange={setXColumn}
                        placeholder={t("ChartView.XColumnPlaceholder")}
                        data-testid="chart-view-x-column"
                      >
                        {xAxisColumns.map((col) => (
                          <SelectItem key={col.name} value={col.name}>
                            {col.name}
                          </SelectItem>
                        ))}
                      </Select>
                      {xAxisColumns.length === 0 && (
                        <p className="mt-1 text-xs text-brand-text-sub">
                          {t("ChartView.NoNumericColumns")}
                        </p>
                      )}
                    </div>

                    {/* Y axis (scatter) */}
                    {chartType === "scatter" && (
                      <div>
                        <label className="mb-1 block text-xs font-medium text-brand-text-main">
                          {t("ChartView.YColumnLabel")}
                        </label>
                        <Select
                          value={yColumn}
                          onValueChange={setYColumn}
                          placeholder={t("ChartView.YColumnPlaceholder")}
                          data-testid="chart-view-y-column"
                        >
                          {yAxisColumns.map((col) => (
                            <SelectItem key={col.name} value={col.name}>
                              {col.name}
                            </SelectItem>
                          ))}
                        </Select>
                        {yAxisColumns.length === 0 && (
                          <p className="mt-1 text-xs text-brand-text-sub">
                            {t("ChartView.NoNumericColumns")}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Y columns (line, multiple) */}
                    {chartType === "line" && (
                      <div className="min-h-0 flex-1">
                        <VariableSelectorField
                          label={t("ChartView.YColumnsLabel")}
                          mode="multiple"
                          columns={yAxisColumns}
                          selectedValues={yColumns}
                          onMultipleChange={setYColumns}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Right: Chart Panel ── */}
          <div
            className="relative flex flex-1 flex-col overflow-hidden rounded-xl border border-border-color bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
            data-testid="chart-view-panel"
          >
            {/* Plotly mount target (always in DOM) */}
            <div ref={plotDivRef} className="absolute inset-0" />

            {/* Empty state overlay */}
            {!hasChartData && !isRendering && (
              <div className="absolute inset-0 flex items-center justify-center">
                <AnalysisEmptyState
                  testId="chart-view-empty"
                  icon={<BarChart2 className="h-10 w-10" />}
                  title={emptyHint.title}
                  description={emptyHint.description}
                  className="max-w-xs"
                />
              </div>
            )}

            {/* Rendering overlay */}
            {isRendering && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/70 dark:bg-gray-800/70">
                <div className="flex items-center gap-2 text-sm text-brand-text-sub">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>{t("ChartView.Loading")}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </PageLayout>
  );
};
