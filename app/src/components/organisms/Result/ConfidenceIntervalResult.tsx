import { getEconomiconAppAPI } from "@/api/endpoints";
import { OutputResultFormat } from "@/api/model/outputResultFormat";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { cn } from "@/lib/utils/helpers";
import type { ConfidenceIntervalResultEntry } from "@/stores/confidenceIntervalResults";
import { Check, Clipboard, FileDown, Loader2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type ConfidenceIntervalResultProps = {
  result: ConfidenceIntervalResultEntry;
};

function formatNumber(value: unknown): string {
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toFixed(4);
  }
  return String(value ?? "—");
}

export const ConfidenceIntervalResult = ({
  result,
}: ConfidenceIntervalResultProps) => {
  const { t } = useTranslation();
  const levelPct = `${(result.confidenceLevel * 100).toFixed(0)}%`;
  const [isOutputDialogOpen, setIsOutputDialogOpen] = useState(false);
  const [isQuickCopying, setIsQuickCopying] = useState(false);
  const [isQuickCopied, setIsQuickCopied] = useState(false);

  const handleQuickCopy = async () => {
    setIsQuickCopying(true);
    try {
      const response = await getEconomiconAppAPI().outputResult({
        resultType: "confidence_interval",
        resultIds: [result.resultId],
        format: OutputResultFormat.markdown,
      });
      if (response.code === "OK" && response.result) {
        await navigator.clipboard.writeText(response.result.content);
        setIsQuickCopied(true);
        setTimeout(() => setIsQuickCopied(false), 2000);
      }
    } finally {
      setIsQuickCopying(false);
    }
  };

  return (
    <>
      <div
        className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden"
        data-testid="confidence-interval-result"
      >
        {/* ヘッダー */}
        <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
          <div className="mb-3 flex justify-end gap-1.5">
            <button
              type="button"
              onClick={() => void handleQuickCopy()}
              disabled={isQuickCopying}
              title={t("ConfidenceIntervalView.QuickCopyMd")}
              className={cn(
                "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                "border border-gray-300 dark:border-gray-600",
                "hover:bg-gray-100 dark:hover:bg-gray-700",
                "disabled:cursor-not-allowed disabled:opacity-50",
                isQuickCopied
                  ? "border-green-500 text-green-600 dark:text-green-400"
                  : "text-gray-600 dark:text-gray-400",
              )}
              data-testid="ci-quick-copy-md-btn"
            >
              {isQuickCopying ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : isQuickCopied ? (
                <Check className="h-3.5 w-3.5" />
              ) : (
                <Clipboard className="h-3.5 w-3.5" />
              )}
              MD
            </button>

            <button
              type="button"
              onClick={() => setIsOutputDialogOpen(true)}
              title={t("ConfidenceIntervalView.OutputDialog")}
              className={cn(
                "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                "border border-gray-300 dark:border-gray-600",
                "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700",
              )}
              data-testid="ci-open-output-dialog-btn"
            >
              <FileDown className="h-3.5 w-3.5" />
              {t("ConfidenceIntervalView.OutputDialog")}
            </button>
          </div>

          <h3 className="text-sm font-semibold text-gray-800">
            {t("ConfidenceIntervalView.Title")}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {result.tableName} / {result.columnName}
          </p>
        </div>

        {/* 結果テーブル */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="px-5 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {t("ConfidenceIntervalView.ResultStatistic")}
                </th>
                <th className="px-5 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {t("ConfidenceIntervalView.ResultStatisticValue")}
                </th>
                <th className="px-5 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {t("ConfidenceIntervalView.ResultConfidenceLevel")}
                </th>
                <th className="px-5 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {t("ConfidenceIntervalView.ResultLower")}
                </th>
                <th className="px-5 py-2.5 text-right text-xs font-medium text-gray-500 uppercase tracking-wide">
                  {t("ConfidenceIntervalView.ResultUpper")}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-50 hover:bg-gray-50/40 transition-colors">
                <td className="px-5 py-3 text-gray-700 font-medium">
                  {t(
                    `ConfidenceIntervalView.StatisticType_${result.statistic.type}`,
                  )}
                </td>
                <td className="px-5 py-3 text-right tabular-nums text-gray-800">
                  {formatNumber(result.statistic.value)}
                </td>
                <td className="px-5 py-3 text-right tabular-nums text-gray-800">
                  {levelPct}
                </td>
                <td className="px-5 py-3 text-right tabular-nums text-gray-800">
                  {formatNumber(result.confidenceInterval?.lower)}
                </td>
                <td className="px-5 py-3 text-right tabular-nums text-gray-800">
                  {formatNumber(result.confidenceInterval?.upper)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <OutputResultDialog
        open={isOutputDialogOpen}
        onOpenChange={setIsOutputDialogOpen}
        resultKind="confidence_interval"
        resultId={result.resultId}
        title={`${result.tableName} / ${result.columnName}`}
      />
    </>
  );
};
