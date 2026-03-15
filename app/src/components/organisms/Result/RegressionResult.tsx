import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import type { LinearRegressionResultType } from "../../../types/commonTypes";
import { ResultSection, StatItem } from "../../molecules/Result/ResultSection";

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
      <ResultSection title={t("RegressionResult.AnalysisSummary")}>
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

      {/* 係数テーブル */}
      <ResultSection title={t("RegressionResult.Coefficients")}>
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
      </ResultSection>

      {/* モデル統計量 */}
      <ResultSection title={t("RegressionResult.ModelStatistics")}>
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
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
        </div>
      </ResultSection>
    </div>
  );
};
