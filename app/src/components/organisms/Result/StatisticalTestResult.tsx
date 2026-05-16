import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail } from "@/api/model";
import { OutputResultFormat } from "@/api/model/outputResultFormat";
import { Tooltip } from "@/components/atoms/Tooltip/Tooltip";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { cn } from "@/lib/utils/helpers";
import { Check, Clipboard, FileDown, Loader2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type StatisticalTestResultData = {
  statistic?: number | null;
  pValue?: number | null;
  df?: number | null;
  df2?: number | null;
  confidenceInterval?: {
    lower?: number | null;
    upper?: number | null;
  } | null;
  confidenceLevel?: number | null;
  effectSize?: number | null;
};

type StatisticalTestResultProps = {
  detail: AnalysisResultDetail;
};

const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return "—";
  if (Number.isInteger(value)) return value.toLocaleString();
  return value.toFixed(4);
};

const inferTestType = (result: StatisticalTestResultData) => {
  if (typeof result.df2 === "number") return "f-test" as const;
  if (result.df === null || result.df === undefined) return "z-test" as const;
  return "t-test" as const;
};

export const StatisticalTestResult = ({
  detail,
}: StatisticalTestResultProps) => {
  const { t } = useTranslation();
  const result = detail.resultData as unknown as StatisticalTestResultData;
  const inferredTestType = inferTestType(result);
  const [isOutputDialogOpen, setIsOutputDialogOpen] = useState(false);
  const [outputDialogSessionKey, setOutputDialogSessionKey] = useState(0);
  const [isQuickCopying, setIsQuickCopying] = useState(false);
  const [isQuickCopied, setIsQuickCopied] = useState(false);

  const handleQuickCopy = async () => {
    setIsQuickCopying(true);
    try {
      const response = await getEconomiconAppAPI().outputResult({
        resultType: "statistical_test",
        resultIds: [detail.id],
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

  const openOutputDialog = () => {
    setOutputDialogSessionKey((prev) => prev + 1);
    setIsOutputDialogOpen(true);
  };

  return (
    <>
      <div
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800"
        data-testid="statistical-test-result"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              {t("StatisticalTestResult.Title")}
            </h3>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              {detail.name}
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <Tooltip content={t("StatisticalTestResult.QuickCopyMd")}>
              <span className="inline-flex">
                <button
                  type="button"
                  onClick={() => void handleQuickCopy()}
                  disabled={isQuickCopying}
                  aria-label={t("StatisticalTestResult.QuickCopyMd")}
                  className={cn(
                    "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                    "border border-gray-300 dark:border-gray-600",
                    "hover:bg-gray-100 dark:hover:bg-gray-700",
                    "disabled:cursor-not-allowed disabled:opacity-50",
                    isQuickCopied
                      ? "border-green-500 text-green-600 dark:text-green-400"
                      : "text-gray-600 dark:text-gray-400",
                  )}
                  data-testid="statistical-test-quick-copy-md-btn"
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
              </span>
            </Tooltip>

            <Tooltip content={t("StatisticalTestResult.OutputDialog")}>
              <span className="inline-flex">
                <button
                  type="button"
                  onClick={openOutputDialog}
                  aria-label={t("StatisticalTestResult.OutputDialog")}
                  className={cn(
                    "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                    "border border-gray-300 dark:border-gray-600",
                    "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700",
                  )}
                  data-testid="statistical-test-open-output-dialog-btn"
                >
                  <FileDown className="h-3.5 w-3.5" />
                  {t("StatisticalTestResult.OutputDialog")}
                </button>
              </span>
            </Tooltip>
          </div>
        </div>

        <dl className="grid gap-3 md:grid-cols-3">
          <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-900/40">
            <dt className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.Type")}
            </dt>
            <dd className="mt-1 text-sm font-medium text-gray-800 dark:text-gray-100">
              {t(`StatisticalTestResult.Type_${inferredTestType}`)}
            </dd>
          </div>
          <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-900/40">
            <dt className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.DataName")}
            </dt>
            <dd className="mt-1 text-sm font-medium text-gray-800 dark:text-gray-100">
              {detail.tableName}
            </dd>
          </div>
          <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-900/40">
            <dt className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.ConfidenceLevel")}
            </dt>
            <dd className="mt-1 text-sm font-medium tabular-nums text-gray-800 dark:text-gray-100">
              {result.confidenceLevel == null
                ? "—"
                : `${(result.confidenceLevel * 100).toFixed(0)}%`}
            </dd>
          </div>
        </dl>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <div className="rounded-md border border-gray-200 px-3 py-2 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.Statistic")}
            </p>
            <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
              {formatNumber(result.statistic)}
            </p>
          </div>
          <div className="rounded-md border border-gray-200 px-3 py-2 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.PValue")}
            </p>
            <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
              {formatNumber(result.pValue)}
            </p>
          </div>
          <div className="rounded-md border border-gray-200 px-3 py-2 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.DF")}
            </p>
            <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
              {formatNumber(result.df)}
            </p>
          </div>
          <div className="rounded-md border border-gray-200 px-3 py-2 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.DF2")}
            </p>
            <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
              {formatNumber(result.df2)}
            </p>
          </div>
          <div className="rounded-md border border-gray-200 px-3 py-2 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.EffectSize")}
            </p>
            <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
              {formatNumber(result.effectSize)}
            </p>
          </div>
        </div>

        {result.confidenceInterval && (
          <div className="rounded-md border border-gray-200 px-3 py-3 dark:border-gray-700">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              {t("StatisticalTestResult.ConfidenceInterval")}
            </h4>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t("StatisticalTestResult.Lower")}
                </p>
                <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
                  {formatNumber(result.confidenceInterval.lower)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t("StatisticalTestResult.Upper")}
                </p>
                <p className="mt-1 font-mono text-sm text-gray-800 dark:text-gray-100">
                  {formatNumber(result.confidenceInterval.upper)}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <OutputResultDialog
        key={`${detail.id}:${outputDialogSessionKey}`}
        open={isOutputDialogOpen}
        onOpenChange={setIsOutputDialogOpen}
        resultKind="statistical_test"
        resultId={detail.id}
        title={detail.name}
      />
    </>
  );
};
