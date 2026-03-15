import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../api/endpoints";
import { DescriptiveStatisticType } from "../../api/model";
import { showMessageDialog } from "../../lib/dialog/message";
import { cn } from "../../lib/utils/helpers";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableListStore } from "../../stores/tableList";
import type { ColumnType } from "../../types/commonTypes";
import { Select, SelectItem } from "../atoms/Input/Select";
import { ActionButtonBar } from "../molecules/ActionBar/ActionButtonBar";
import { CheckboxTagGroup } from "../molecules/Field/CheckboxTagGroup";
import { FormField } from "../molecules/Form/FormField";
import { PageLayout } from "../templates/PageLayout";

// ---------------------------------------------------------------------------
// Type assertions for the API response (statistics: unknown → StatisticsMap)
// ---------------------------------------------------------------------------
type StatKey = DescriptiveStatisticType;
type StatCellValue = number | string | number[] | null;
type StatRow = Partial<Record<StatKey, StatCellValue>>;
type StatisticsMap = Record<string, StatRow>;

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const ALL_STAT_TYPES: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.mode,
  DescriptiveStatisticType.variance,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.range,
  DescriptiveStatisticType.iqr,
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatStatValue(val: StatCellValue | undefined): string {
  if (val === null || val === undefined) return "—";
  if (Array.isArray(val)) return val.join(", ");
  if (typeof val === "number") {
    if (Number.isInteger(val)) return val.toLocaleString();
    return val.toFixed(4);
  }
  return String(val);
}

type FormErrors = {
  table?: string;
  columns?: string;
  stats?: string;
};

type ResultSnapshot = {
  data: StatisticsMap;
  cols: string[];
  stats: DescriptiveStatisticType[];
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export const DescriptiveStatistics = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((s) => s.tableList);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const [selectedTable, setSelectedTable] = useState("");
  const [columns, setColumns] = useState<ColumnType[]>([]);
  const [checkedCols, setCheckedCols] = useState<Set<string>>(new Set());
  const [checkedStats, setCheckedStats] = useState<
    Set<DescriptiveStatisticType>
  >(new Set(ALL_STAT_TYPES));
  const resultRef = useRef<HTMLDivElement>(null);
  const [isLoadingCols, setIsLoadingCols] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [result, setResult] = useState<ResultSnapshot | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});

  /* ── Fetch columns when table changes ────────────────────── */
  useEffect(() => {
    if (!selectedTable) {
      setColumns([]);
      setCheckedCols(new Set());
      setResult(null);
      return;
    }
    setIsLoadingCols(true);
    setResult(null);
    const api = getEconomiconAPI();
    api
      .getColumnList({ tableName: selectedTable })
      .then((resp) => {
        if (resp.code === "OK") {
          setColumns(resp.result.columnInfoList);
          setCheckedCols(
            new Set(resp.result.columnInfoList.map((c: ColumnType) => c.name)),
          );
        }
      })
      .catch(() => {})
      .finally(() => setIsLoadingCols(false));
  }, [selectedTable]);

  /* ── Toggle helpers ──────────────────────────────────────── */
  const toggleCol = (name: string) => {
    setCheckedCols((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const toggleStat = (stat: DescriptiveStatisticType) => {
    setCheckedStats((prev) => {
      const next = new Set(prev);
      if (next.has(stat)) next.delete(stat);
      else next.add(stat);
      return next;
    });
  };

  /* ── Submit ──────────────────────────────────────────────── */
  const handleSubmit = async () => {
    const newErrors: FormErrors = {};
    if (!selectedTable)
      newErrors.table = t("DescriptiveStatistics.ErrorDataRequired");
    if (checkedCols.size === 0)
      newErrors.columns = t("DescriptiveStatistics.ErrorColumnsRequired");
    if (checkedStats.size === 0)
      newErrors.stats = t("DescriptiveStatistics.ErrorStatsRequired");

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    setErrors({});

    const orderedCols = columns
      .map((c) => c.name)
      .filter((n) => checkedCols.has(n));
    const orderedStats = ALL_STAT_TYPES.filter((s) => checkedStats.has(s));

    setIsCalculating(true);
    try {
      const api = getEconomiconAPI();
      const resp = await api.descriptiveStatistics({
        tableName: selectedTable,
        columnNameList: orderedCols,
        statistics: orderedStats,
      });
      if (resp.code === "OK") {
        const data = resp.result.statistics as StatisticsMap;
        setResult({ data, cols: orderedCols, stats: orderedStats });
        setTimeout(
          () =>
            resultRef.current?.scrollIntoView({
              behavior: "smooth",
              block: "start",
            }),
          50,
        );
      }
    } catch {
      await showMessageDialog(
        t("DescriptiveStatistics.ErrorCalculation"),
        "error",
      );
    } finally {
      setIsCalculating(false);
    }
  };

  /* ── Render ──────────────────────────────────────────────── */
  return (
    <PageLayout
      title={t("DescriptiveStatistics.Title")}
      description={t("DescriptiveStatistics.Description")}
    >
      <div className="flex-1 overflow-y-auto min-h-0 space-y-4 pb-2">
        {/* ─── 1. Table selection ────────────────────────────── */}
        <FormField
          label={t("DescriptiveStatistics.DataLabel")}
          error={errors.table}
        >
          <Select
            value={selectedTable}
            onValueChange={(v) => {
              setSelectedTable(v);
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

        {/* ─── 2. Column selection ───────────────────────────── */}
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
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() =>
                      setCheckedCols(new Set(columns.map((c) => c.name)))
                    }
                    className="text-xs text-brand-accent hover:underline"
                  >
                    {t("DescriptiveStatistics.SelectAll")}
                  </button>
                  <span className="text-xs text-brand-text-sub">/</span>
                  <button
                    type="button"
                    onClick={() => setCheckedCols(new Set())}
                    className="text-xs text-brand-accent hover:underline"
                  >
                    {t("DescriptiveStatistics.DeselectAll")}
                  </button>
                </div>
                <CheckboxTagGroup
                  items={columns.map((c) => ({ value: c.name, label: c.name }))}
                  checked={checkedCols}
                  onToggle={toggleCol}
                  error={errors.columns}
                />
              </div>
            )}
          </FormField>
        )}

        {/* ─── 3. Statistics selection ───────────────────────── */}
        <FormField label={t("DescriptiveStatistics.StatisticsLabel")}>
          <div className="space-y-2">
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setCheckedStats(new Set(ALL_STAT_TYPES))}
                className="text-xs text-brand-accent hover:underline"
              >
                {t("DescriptiveStatistics.SelectAll")}
              </button>
              <span className="text-xs text-brand-text-sub">/</span>
              <button
                type="button"
                onClick={() => setCheckedStats(new Set())}
                className="text-xs text-brand-accent hover:underline"
              >
                {t("DescriptiveStatistics.DeselectAll")}
              </button>
            </div>
            <CheckboxTagGroup
              items={ALL_STAT_TYPES.map((s) => ({
                value: s,
                label: t(`DescriptiveStatistics.Stat_${s}`),
              }))}
              checked={checkedStats as Set<string>}
              onToggle={(v) => toggleStat(v as DescriptiveStatisticType)}
              error={errors.stats}
            />
          </div>
        </FormField>

        {/* ─── 4. Submit ─────────────────────────────────────── */}
        {/* ActionButtonBar は最下部に移動済み */}

        {/* ─── 5. Result table ───────────────────────────────── */}
        {result && (
          <div ref={resultRef} className="space-y-2 pb-4">
            <h2 className="text-sm font-semibold text-brand-text-main">
              {t("DescriptiveStatistics.ResultTitle")}
            </h2>
            <div className="overflow-x-auto rounded-lg border border-border-color">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-brand-secondary border-b border-border-color">
                    <th className="px-4 py-2.5 text-left font-medium text-brand-text-sub whitespace-nowrap sticky left-0 bg-brand-secondary">
                      {t("DescriptiveStatistics.Column")}
                    </th>
                    {result.stats.map((stat) => (
                      <th
                        key={stat}
                        className="px-4 py-2.5 text-right font-medium text-brand-text-sub whitespace-nowrap"
                      >
                        {t(`DescriptiveStatistics.Stat_${stat}`)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.cols.map((col, i) => (
                    <tr
                      key={col}
                      className={cn(
                        "border-b border-border-color last:border-0 transition-colors",
                        i % 2 === 0
                          ? "bg-white dark:bg-brand-primary"
                          : "bg-brand-secondary/40",
                      )}
                    >
                      <td className="px-4 py-2 font-medium text-brand-text-main sticky left-0 bg-inherit whitespace-nowrap">
                        {col}
                      </td>
                      {result.stats.map((stat) => (
                        <td
                          key={stat}
                          className="px-4 py-2 text-right font-mono text-brand-text-main tabular-nums"
                        >
                          {formatStatValue(result.data[col]?.[stat])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      <ActionButtonBar
        cancelText={t("Common.Cancel")}
        selectText={
          isCalculating
            ? t("DescriptiveStatistics.Processing")
            : t("DescriptiveStatistics.RunCalculation")
        }
        onCancel={() => setCurrentView("DataPreview")}
        onSelect={handleSubmit}
      />
    </PageLayout>
  );
};
