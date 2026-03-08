import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import type { LinearRegressionResultType } from "../../../types/commonTypes";

type RegressionResultProps = {
  result: LinearRegressionResultType;
  className?: string;
};

export const RegressionResult = ({
  result,
  className,
}: RegressionResultProps) => {
  const { t } = useTranslation();

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

  return (
    <div className={cn("flex flex-col gap-4 p-4", className)}>
      {/* 分析概要 */}
      <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
        <h3 className="mb-3 text-base font-bold text-text-heading">
          {t("RegressionResult.AnalysisSummary")}
        </h3>
        <div className="grid grid-cols-1 gap-x-8 gap-y-2 text-sm md:grid-cols-2">
          <div className="flex gap-2">
            <span className="font-medium text-brand-text-main shrink-0">
              {t("RegressionResult.TableName")}:
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
      </div>

      {/* 係数テーブル */}
      <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-base font-bold text-text-heading">
          {t("RegressionResult.Coefficients")}
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10">
              <tr className="border-b border-border-color bg-secondary">
                <th className="px-3 py-2 text-left font-semibold text-text-heading">
                  {t("RegressionResult.Variable")}
                </th>
                <th className="px-3 py-2 text-right font-semibold text-text-heading">
                  {t("RegressionResult.Coefficient")}
                </th>
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
              {result.parameters.map((param, index) => (
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
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-right text-xs text-brand-text-main/50">
          {t("RegressionResult.SignificanceNote")}
        </p>
      </div>

      {/* モデル統計量 */}
      <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-base font-bold text-text-heading">
          {t("RegressionResult.ModelStatistics")}
        </h3>
        {/* R² / 調整済みR² を強調 */}
        <div className="mb-3 grid grid-cols-2 gap-3">
          <div className="flex flex-col rounded-lg bg-brand-accent/5 p-3">
            <span className="text-xs font-medium text-brand-accent/70">R²</span>
            <span className="mt-0.5 text-2xl font-bold text-brand-accent">
              {formatNumber(result.modelStatistics.R2)}
            </span>
          </div>
          <div className="flex flex-col rounded-lg bg-brand-accent/5 p-3">
            <span className="text-xs font-medium text-brand-accent/70">
              {t("RegressionResult.AdjustedR2")}
            </span>
            <span className="mt-0.5 text-2xl font-bold text-brand-accent">
              {formatNumber(result.modelStatistics.adjustedR2)}
            </span>
          </div>
        </div>
        {/* その他の統計量 */}
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">AIC</span>
            <span className="font-semibold text-brand-text-main">
              {formatNumber(result.modelStatistics.AIC)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">BIC</span>
            <span className="font-semibold text-brand-text-main">
              {formatNumber(result.modelStatistics.BIC)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">
              {t("RegressionResult.FValue")}
            </span>
            <span className="font-semibold text-brand-text-main">
              {formatNumber(result.modelStatistics.fValue)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">
              {t("RegressionResult.FProbability")}
            </span>
            <span className="font-semibold text-brand-text-main">
              {formatNumber(result.modelStatistics.fProbability)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">
              {t("RegressionResult.LogLikelihood")}
            </span>
            <span className="font-semibold text-brand-text-main">
              {formatNumber(result.modelStatistics.logLikelihood)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-brand-text-main/60">
              {t("RegressionResult.Observations")}
            </span>
            <span className="font-semibold text-brand-text-main">
              {result.modelStatistics.nObservations}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
