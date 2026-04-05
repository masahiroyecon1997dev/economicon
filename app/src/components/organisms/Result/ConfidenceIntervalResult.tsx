import type { ConfidenceIntervalResultEntry } from "@/stores/confidenceIntervalResults";
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

  return (
    <div
      className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden"
      data-testid="confidence-interval-result"
    >
      {/* ヘッダー */}
      <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
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
  );
};
