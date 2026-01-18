import { useTranslation } from "react-i18next";
import { cn } from "../../../functions/utils";
import type { LinearRegressionResultType } from "../../../types/commonTypes";

type RegressionResultProps = {
  result: LinearRegressionResultType;
  className?: string;
};

export const RegressionResult = ({ result, className }: RegressionResultProps) => {
  const { t } = useTranslation();

  const formatNumber = (num: number, decimals: number = 4): string => {
    return num.toFixed(decimals);
  };

  return (
    <div className={cn("flex flex-col gap-4 p-4", className)}>
      {/* 分析概要 */}
      <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-base font-bold text-text-heading">
          {t("RegressionResult.AnalysisSummary")}
        </h3>
        <div className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
          <div className="flex justify-between">
            <span className="font-medium text-text-main">{t("RegressionResult.TableName")}:</span>
            <span className="text-text-main">{result.tableName}</span>
          </div>
          <div className="flex justify-between">
            <span className="font-medium text-text-main">{t("RegressionResult.DependentVariable")}:</span>
            <span className="text-text-main">{result.dependentVariable}</span>
          </div>
          <div className="col-span-1 md:col-span-2">
            <span className="font-medium text-text-main">{t("RegressionResult.ExplanatoryVariables")}:</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {result.explanatoryVariables.map((variable, index) => (
                <span
                  key={index}
                  className="rounded-md bg-accent px-2 py-0.5 text-xs text-white"
                >
                  {variable}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* モデル統計量 */}
      <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-base font-bold text-text-heading">
          {t("RegressionResult.ModelStatistics")}
        </h3>
        <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">R²</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.R2)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">{t("RegressionResult.AdjustedR2")}</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.adjustedR2)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">AIC</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.AIC)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">BIC</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.BIC)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">{t("RegressionResult.FValue")}</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.fValue)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">{t("RegressionResult.FProbability")}</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.fProbability)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">{t("RegressionResult.LogLikelihood")}</span>
            <span className="font-semibold text-text-main">
              {formatNumber(result.modelStatistics.logLikelihood)}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-text-main/60">{t("RegressionResult.Observations")}</span>
            <span className="font-semibold text-text-main">
              {result.modelStatistics.nObservations}
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
            <thead>
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
              </tr>
            </thead>
            <tbody>
              {result.parameters.map((param, index) => (
                <tr
                  key={index}
                  className="border-b border-border-color hover:bg-secondary/50"
                >
                  <td className="px-3 py-2 font-medium text-text-main">
                    {param.variable}
                  </td>
                  <td className="px-3 py-2 text-right text-text-main">
                    {formatNumber(param.coefficient)}
                  </td>
                  <td className="px-3 py-2 text-right text-text-main">
                    {formatNumber(param.standardError)}
                  </td>
                  <td className="px-3 py-2 text-right text-text-main">
                    {formatNumber(param.tValue)}
                  </td>
                  <td
                    className={cn(
                      "px-3 py-2 text-right font-medium",
                      param.pValue < 0.001
                        ? "text-green-600"
                        : param.pValue < 0.01
                          ? "text-green-500"
                          : param.pValue < 0.05
                            ? "text-yellow-600"
                            : "text-text-main"
                    )}
                  >
                    {formatNumber(param.pValue)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 回帰結果の詳細 */}
      {result.regressionResult && (
        <div className="rounded-xl border border-border-color bg-white p-4 shadow-sm">
          <h3 className="mb-3 text-base font-bold text-text-heading">
            {t("RegressionResult.RegressionDetails")}
          </h3>
          <pre className="overflow-x-auto rounded bg-secondary p-3 text-xs text-text-main">
            {result.regressionResult}
          </pre>
        </div>
      )}
    </div>
  );
};
