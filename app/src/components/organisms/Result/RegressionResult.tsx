import { getEconomiconAppAPI } from "@/api/endpoints";
import { OutputResultFormat } from "@/api/model/outputResultFormat";
import { RegressionOutputOptionsStatInParentheses } from "@/api/model/regressionOutputOptionsStatInParentheses";
import { Tooltip } from "@/components/atoms/Tooltip/Tooltip";
import { ExplainerButton } from "@/components/molecules/Dialog/ExplainerButton";
import {
  ResultSection,
  StatItem,
} from "@/components/molecules/Result/ResultSection";
import { AddDiagnosticColumnsDialog } from "@/components/organisms/Dialog/AddDiagnosticColumnsDialog";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { TobitDiagnostics } from "@/components/organisms/Result/TobitDiagnostics";
import { cn } from "@/lib/utils/helpers";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import {
  Check,
  Clipboard,
  FileDown,
  HelpCircle,
  Loader2,
  PlusCircle,
} from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type RegressionResultProps = {
  result: LinearRegressionResultType;
  className?: string;
};

export const RegressionResult = ({
  result,
  className,
}: RegressionResultProps) => {
  const { t } = useTranslation();
  const [isOutputDialogOpen, setIsOutputDialogOpen] = useState(false);
  const [outputDialogSessionKey, setOutputDialogSessionKey] = useState(0);
  const [isQuickCopying, setIsQuickCopying] = useState(false);
  const [isQuickCopied, setIsQuickCopied] = useState(false);
  const [isDiagnosticDialogOpen, setIsDiagnosticDialogOpen] = useState(false);

  const formatNumber = (
    num: number | null | undefined,
    decimals: number = 4,
  ): string => {
    if (num === null || num === undefined) return t("RegressionResult.NA");
    return num.toFixed(decimals);
  };

  const significanceMarker = (pValue: number | null | undefined): string => {
    if (pValue === null || pValue === undefined) return "";
    if (pValue < 0.001) return "***";
    if (pValue < 0.01) return "**";
    if (pValue < 0.05) return "*";
    return "";
  };

  const handleQuickCopy = async () => {
    setIsQuickCopying(true);
    try {
      const response = await getEconomiconAppAPI().outputResult({
        resultType: "regression",
        resultIds: [result.resultId],
        format: OutputResultFormat.markdown,
        options: {
          statInParentheses: RegressionOutputOptionsStatInParentheses.se,
        },
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

  const isDiscreteModel = result.modelStatistics.pseudoRSquared !== undefined;
  const hasMarginalEffects =
    result.marginalEffects && result.marginalEffects.length > 0;

  const getMarginalEffect = (variable: string) =>
    result.marginalEffects?.find((m) => m.variable === variable);

  return (
    <div className={cn("flex flex-col gap-4 p-2", className)}>
      {/* 分析概要 */}
      <ResultSection title={t("RegressionResult.AnalysisSummary")}>
        {/* ── ヘッダー右端: 出力ボタン群 ── */}
        <div className="mb-3 flex justify-end gap-1.5">
          {!isDiscreteModel && (
            <Tooltip content={t("RegressionResult.AddDiagnosticColumns")}>
              <span className="inline-flex">
                <button
                  type="button"
                  onClick={() => setIsDiagnosticDialogOpen(true)}
                  aria-label={t("RegressionResult.AddDiagnosticColumns")}
                  className={cn(
                    "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                    "border border-gray-300 dark:border-gray-600",
                    "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700",
                  )}
                  data-testid="add-diagnostic-columns-btn"
                >
                  <PlusCircle className="h-3.5 w-3.5" />
                  {t("RegressionResult.AddDiagnosticColumns")}
                </button>
              </span>
            </Tooltip>
          )}

          <Tooltip content={t("RegressionResult.QuickCopyMd")}>
            <span className="inline-flex">
              <button
                type="button"
                onClick={() => void handleQuickCopy()}
                disabled={isQuickCopying}
                aria-label={t("RegressionResult.QuickCopyMd")}
                className={cn(
                  "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                  "border border-gray-300 dark:border-gray-600",
                  "hover:bg-gray-100 dark:hover:bg-gray-700",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  isQuickCopied
                    ? "border-green-500 text-green-600 dark:text-green-400"
                    : "text-gray-600 dark:text-gray-400",
                )}
                data-testid="quick-copy-md-btn"
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

          <Tooltip content={t("RegressionResult.OutputDialog")}>
            <span className="inline-flex">
              <button
                type="button"
                onClick={openOutputDialog}
                aria-label={t("RegressionResult.OutputDialog")}
                className={cn(
                  "inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-colors",
                  "border border-gray-300 dark:border-gray-600",
                  "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700",
                )}
                data-testid="open-output-dialog-btn"
              >
                <FileDown className="h-3.5 w-3.5" />
                {t("RegressionResult.OutputDialog")}
              </button>
            </span>
          </Tooltip>
        </div>

        <div className="grid grid-cols-1 gap-x-8 gap-y-2 text-sm md:grid-cols-2">
          <div className="flex gap-2">
            <span className="font-medium text-brand-text-main shrink-0">
              {t("RegressionResult.DataName")}:
            </span>
            <span className="text-brand-text-main break-all">
              {result.tableName}
            </span>
          </div>
          <div className="flex gap-2">
            <span className="font-medium text-brand-text-main shrink-0">
              {t("RegressionResult.DependentVariable")}:
            </span>
            <span className="text-brand-text-main break-all">
              {result.dependentVariable}
            </span>
          </div>
        </div>
      </ResultSection>

      {/* 出力ダイアログ */}
      <OutputResultDialog
        key={`${result.resultId}:${outputDialogSessionKey}`}
        open={isOutputDialogOpen}
        onOpenChange={setIsOutputDialogOpen}
        resultKind="regression"
        result={result}
      />

      {/* 診断列追加ダイアログ */}
      <AddDiagnosticColumnsDialog
        open={isDiagnosticDialogOpen}
        onOpenChange={setIsDiagnosticDialogOpen}
        resultId={result.resultId}
        defaultTableName={result.tableName}
      />

      {/* 係数テーブル */}
      <ResultSection
        title={t("RegressionResult.Coefficients")}
        titleAction={
          <ExplainerButton
            explainerKey={
              result.modelType === "wls"
                ? "wls_result_coefficients"
                : "ols_result_coefficients"
            }
            aria-label={t("RegressionResult.CoefficientsExplainerLabel")}
            data-testid="coefficients-explainer-btn"
          >
            <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
          </ExplainerButton>
        }
      >
        <div className="app-scrollbar overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-border-color bg-secondary">
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.Variable")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.Coefficient")}
                </th>
                {hasMarginalEffects && (
                  <th className="px-3 py-2 text-right font-semibold text-text-heading">
                    {t("RegressionResult.MarginalEffect")}
                  </th>
                )}
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.StandardError")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.TValue")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.PValue")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.ConfidenceIntervalLower")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.ConfidenceIntervalUpper")}
                </th>
              </tr>
            </thead>
            <tbody>
              {result.parameters.map((param, index) => {
                const ame = getMarginalEffect(param.variable);
                return (
                  <tr
                    key={index}
                    className="border-b border-border-color hover:bg-secondary/50"
                  >
                    <td className="px-3 py-2 font-medium text-brand-text-main">
                      {param.variable}
                    </td>
                    <td className="px-3 py-2 text-right text-brand-text-main">
                      {formatNumber(param.coefficient)}
                    </td>
                    {hasMarginalEffects && (
                      <td className="px-3 py-2 text-right text-brand-text-main">
                        {ame
                          ? formatNumber(ame.marginalEffect)
                          : t("RegressionResult.NA")}
                      </td>
                    )}
                    <td className="px-3 py-2 text-right text-brand-text-main">
                      {formatNumber(param.standardError)}
                    </td>
                    <td className="px-3 py-2 text-right text-brand-text-main">
                      {formatNumber(param.tValue)}
                    </td>
                    <td
                      className={cn(
                        "px-3 py-2 text-right font-medium",
                        param.pValue !== null && param.pValue < 0.001
                          ? "text-green-600"
                          : param.pValue !== null && param.pValue < 0.01
                            ? "text-green-500"
                            : param.pValue !== null && param.pValue < 0.05
                              ? "text-yellow-600"
                              : "text-brand-text-main",
                      )}
                    >
                      {formatNumber(param.pValue)}
                      {significanceMarker(param.pValue) && (
                        <span className="ml-1 font-bold">
                          {significanceMarker(param.pValue)}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right text-brand-text-main">
                      {formatNumber(param.confidenceIntervalLower)}
                    </td>
                    <td className="px-3 py-2 text-right text-brand-text-main">
                      {formatNumber(param.confidenceIntervalUpper)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-right text-xs text-brand-text-main/50">
          {t("RegressionResult.SignificanceNote")}
        </p>
      </ResultSection>

      {/* モデル統計量 */}
      <ResultSection
        title={t("RegressionResult.ModelStatistics")}
        titleAction={
          <ExplainerButton
            explainerKey={
              result.modelType === "wls"
                ? "wls_result_model_stats"
                : "ols_result_model_stats"
            }
            aria-label={t("RegressionResult.ModelStatisticsExplainerLabel")}
            data-testid="model-stats-explainer-btn"
          >
            <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
          </ExplainerButton>
        }
      >
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
          {isDiscreteModel ? (
            <>
              <StatItem
                label={t("RegressionResult.PseudoR2")}
                value={formatNumber(result.modelStatistics.pseudoRSquared)}
              />
              <StatItem
                label={t("RegressionResult.LogLikelihood")}
                value={formatNumber(result.modelStatistics.logLikelihood)}
              />
              <StatItem
                label={t("RegressionResult.LogLikelihoodNull")}
                value={formatNumber(result.modelStatistics.logLikelihoodNull)}
              />
              <StatItem
                label={t("RegressionResult.LRStatistic")}
                value={formatNumber(result.modelStatistics.lrStatistic)}
              />
              <StatItem
                label={t("RegressionResult.LRDf")}
                value={result.modelStatistics.lrDf ?? t("RegressionResult.NA")}
              />
              <StatItem
                label={t("RegressionResult.LRPValue")}
                value={formatNumber(result.modelStatistics.lrPValue)}
              />
              <StatItem
                label="AIC"
                value={formatNumber(result.modelStatistics.AIC)}
              />
              <StatItem
                label="BIC"
                value={formatNumber(result.modelStatistics.BIC)}
              />
              <StatItem
                label={t("RegressionResult.Observations")}
                value={result.modelStatistics.nObservations}
              />
            </>
          ) : (
            <>
              <StatItem
                label="R²"
                value={formatNumber(result.modelStatistics.R2)}
              />
              <StatItem
                label={t("RegressionResult.AdjustedR2")}
                value={formatNumber(result.modelStatistics.adjustedR2)}
              />
              <StatItem
                label="AIC"
                value={formatNumber(result.modelStatistics.AIC)}
              />
              <StatItem
                label="BIC"
                value={formatNumber(result.modelStatistics.BIC)}
              />
              <StatItem
                label={t("RegressionResult.FValue")}
                value={formatNumber(result.modelStatistics.fValue)}
              />
              <StatItem
                label={t("RegressionResult.FProbability")}
                value={formatNumber(result.modelStatistics.fProbability)}
              />
              <StatItem
                label={t("RegressionResult.LogLikelihood")}
                value={formatNumber(result.modelStatistics.logLikelihood)}
              />
              <StatItem
                label={t("RegressionResult.Observations")}
                value={result.modelStatistics.nObservations}
              />
            </>
          )}
        </div>
      </ResultSection>

      {/* パネルモデル固有統計量（FE / RE） */}
      {result.modelStatistics.R2Within !== undefined && (
        <ResultSection
          title={t("RegressionResult.PanelModelStatistics")}
          titleAction={
            <ExplainerButton
              explainerKey="fe_method"
              aria-label={t(
                "RegressionResult.PanelModelStatisticsExplainerLabel",
              )}
              data-testid="panel-stats-explainer-btn"
            >
              <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
            </ExplainerButton>
          }
        >
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
            <StatItem
              label={t("RegressionResult.R2Within")}
              value={formatNumber(result.modelStatistics.R2Within)}
            />
            <StatItem
              label={t("RegressionResult.R2Between")}
              value={formatNumber(result.modelStatistics.R2Between)}
            />
            <StatItem
              label={t("RegressionResult.R2Overall")}
              value={formatNumber(result.modelStatistics.R2Overall)}
            />
            {result.modelStatistics.nEntities !== undefined && (
              <StatItem
                label={t("RegressionResult.NEntities")}
                value={result.modelStatistics.nEntities}
              />
            )}
            {result.modelStatistics.fPooled !== undefined && (
              <>
                <StatItem
                  label={t("RegressionResult.FPooledStatistic")}
                  value={formatNumber(result.modelStatistics.fPooled.statistic)}
                />
                <StatItem
                  label={t("RegressionResult.FPooledPValue")}
                  value={formatNumber(result.modelStatistics.fPooled.pValue)}
                />
              </>
            )}
          </div>
        </ResultSection>
      )}

      {/* Tobit 診断統計量 */}
      {result.modelType === "tobit" && result.diagnostics && (
        <TobitDiagnostics
          diagnostics={result.diagnostics}
          formatNumber={formatNumber}
        />
      )}
    </div>
  );
};
