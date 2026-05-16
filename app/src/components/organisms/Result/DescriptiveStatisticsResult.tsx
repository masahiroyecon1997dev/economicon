import { DescriptiveStatisticType } from "@/api/model";
import { Tooltip } from "@/components/atoms/Tooltip/Tooltip";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { cn } from "@/lib/utils/helpers";
import { Check, Clipboard, Loader2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type StatCellValue = number | string | number[] | null;
type StatisticsMap = Record<string, Record<string, StatCellValue>>;
type StatisticKey = DescriptiveStatisticType | string;

type DescriptiveStatisticsResultProps = {
  resultId: string;
  tableName: string;
  statistics: StatisticsMap;
  columnNameList?: string[];
  statisticOrder?: string[];
};

const CANONICAL_STAT_ORDER: DescriptiveStatisticType[] = [
  DescriptiveStatisticType.count,
  DescriptiveStatisticType.null_count,
  DescriptiveStatisticType.null_ratio,
  DescriptiveStatisticType.mean,
  DescriptiveStatisticType.median,
  DescriptiveStatisticType.mode,
  DescriptiveStatisticType.variance,
  DescriptiveStatisticType.population_variance,
  DescriptiveStatisticType.std_dev,
  DescriptiveStatisticType.min,
  DescriptiveStatisticType.max,
  DescriptiveStatisticType.range,
  DescriptiveStatisticType.iqr,
  DescriptiveStatisticType.skewness,
  DescriptiveStatisticType.kurtosis,
];

const formatStatValue = (value: StatCellValue | undefined): string => {
  if (value === null || value === undefined) return "-";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toFixed(4);
  }
  return String(value);
};

const getOrderedColumns = (
  statistics: StatisticsMap,
  columnNameList?: string[],
): string[] => {
  const availableColumns = Object.keys(statistics);
  if (!columnNameList?.length) {
    return availableColumns;
  }

  const includedColumns = columnNameList.filter(
    (columnName) => columnName in statistics,
  );
  const remainingColumns = availableColumns.filter(
    (columnName) => !includedColumns.includes(columnName),
  );

  return [...includedColumns, ...remainingColumns];
};

const getOrderedStatisticKeys = (
  statistics: StatisticsMap,
  columns: string[],
  statisticOrder?: string[],
): StatisticKey[] => {
  const discoveredKeys: string[] = [];

  columns.forEach((columnName) => {
    Object.keys(statistics[columnName] ?? {}).forEach((statKey) => {
      if (!discoveredKeys.includes(statKey)) {
        discoveredKeys.push(statKey);
      }
    });
  });

  const prioritizedKeys = statisticOrder?.length
    ? statisticOrder
    : CANONICAL_STAT_ORDER;
  const knownKeys = prioritizedKeys.filter((statKey) =>
    discoveredKeys.includes(statKey),
  );
  const remainingKeys = discoveredKeys.filter(
    (statKey) => !knownKeys.includes(statKey),
  );

  return [...knownKeys, ...remainingKeys];
};

export const DescriptiveStatisticsResult = ({
  resultId,
  tableName,
  statistics,
  columnNameList,
  statisticOrder,
}: DescriptiveStatisticsResultProps) => {
  const { t } = useTranslation();
  const [isOutputDialogOpen, setIsOutputDialogOpen] = useState(false);
  const [outputDialogSessionKey, setOutputDialogSessionKey] = useState(0);
  const [isQuickCopying, setIsQuickCopying] = useState(false);
  const [isQuickCopied, setIsQuickCopied] = useState(false);

  const columns = getOrderedColumns(statistics, columnNameList);
  const statKeys = getOrderedStatisticKeys(statistics, columns, statisticOrder);

  const getStatLabel = (statKey: StatisticKey): string => {
    const translationKey = `DescriptiveStatistics.Stat_${statKey}`;
    const translated = t(translationKey);
    return translated === translationKey ? statKey : translated;
  };

  const handleQuickCopy = async () => {
    setIsQuickCopying(true);
    try {
      setOutputDialogSessionKey((prev) => prev + 1);
      setIsQuickCopied(true);
      setTimeout(() => setIsQuickCopied(false), 2000);
      setIsOutputDialogOpen(true);
    } finally {
      setIsQuickCopying(false);
    }
  };

  return (
    <>
      <div className="space-y-3" data-testid="descriptive-statistics-result">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-brand-text-main">
              {t("DescriptiveStatistics.ResultTitle")}
            </h2>
            <p className="text-xs text-brand-text-sub">{tableName}</p>
          </div>
          <div className="flex items-center gap-1.5">
            <Tooltip content={t("DescriptiveStatistics.OutputDialog")}>
              <span className="inline-flex">
                <button
                  type="button"
                  onClick={() => void handleQuickCopy()}
                  disabled={isQuickCopying}
                  className={cn(
                    "inline-flex items-center gap-1 rounded px-2.5 py-1.5 text-xs font-medium transition-colors",
                    "border border-gray-300 dark:border-gray-600",
                    isQuickCopied
                      ? "bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                      : "bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                  )}
                  aria-label={t("DescriptiveStatistics.OutputDialog")}
                  data-testid="analysis-result-output-button"
                >
                  {isQuickCopying ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : isQuickCopied ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : (
                    <Clipboard className="h-3.5 w-3.5" />
                  )}
                  {t("DescriptiveStatistics.OutputDialog")}
                </button>
              </span>
            </Tooltip>
          </div>
        </div>

        <div className="app-scrollbar overflow-x-auto rounded-lg border border-border-color bg-white dark:bg-brand-primary">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-border-color bg-brand-secondary">
                <th className="sticky left-0 whitespace-nowrap bg-brand-secondary px-4 py-2.5 text-left font-medium text-brand-text-sub">
                  {t("DescriptiveStatistics.Column")}
                </th>
                {statKeys.map((statKey) => (
                  <th
                    key={statKey}
                    className="whitespace-nowrap px-4 py-2.5 text-right font-medium text-brand-text-sub"
                  >
                    {getStatLabel(statKey)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns.map((column, index) => (
                <tr
                  key={column}
                  className={cn(
                    "border-b border-border-color last:border-0",
                    index % 2 === 0
                      ? "bg-white dark:bg-brand-primary"
                      : "bg-brand-secondary",
                  )}
                >
                  <td
                    className={cn(
                      "sticky left-0 whitespace-nowrap px-4 py-2 font-medium text-brand-text-main",
                      index % 2 === 0
                        ? "bg-white dark:bg-brand-primary"
                        : "bg-brand-secondary",
                    )}
                  >
                    {column}
                  </td>
                  {statKeys.map((statKey) => (
                    <td
                      key={statKey}
                      className="px-4 py-2 text-right font-mono tabular-nums text-brand-text-main"
                    >
                      {formatStatValue(statistics[column]?.[statKey])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <OutputResultDialog
        key={`${resultId}:${outputDialogSessionKey}`}
        open={isOutputDialogOpen}
        onOpenChange={setIsOutputDialogOpen}
        resultKind="descriptive_statistics"
        resultId={resultId}
        title={tableName}
      />
    </>
  );
};
