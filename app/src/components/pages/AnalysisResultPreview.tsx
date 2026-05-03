import type { AnalysisResultDetail } from "@/api/model";
import { ConfidenceIntervalResult } from "@/components/organisms/Result/ConfidenceIntervalResult";
import { DescriptiveStatisticsResult } from "@/components/organisms/Result/DescriptiveStatisticsResult";
import { RegressionResult } from "@/components/organisms/Result/RegressionResult";
import { PageLayout } from "@/components/templates/PageLayout";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import type { ConfidenceIntervalResultEntry } from "@/stores/confidenceIntervalResults";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import { Pencil } from "lucide-react";
import { useTranslation } from "react-i18next";

type StatisticsMap = Record<
  string,
  Record<string, number | string | number[] | null>
>;

const toRegressionResult = (
  detail: AnalysisResultDetail,
): LinearRegressionResultType => {
  return {
    ...(detail.resultData as unknown as LinearRegressionResultType),
    resultId: detail.id,
  };
};

const toConfidenceIntervalResult = (
  detail: AnalysisResultDetail,
): ConfidenceIntervalResultEntry => {
  return {
    ...(detail.resultData as unknown as Omit<
      ConfidenceIntervalResultEntry,
      "resultId"
    >),
    resultId: detail.id,
  };
};

type AnalysisResultPanelProps = {
  detail: AnalysisResultDetail | null;
  isLoading?: boolean;
  onEdit?: () => void;
};

export const AnalysisResultPanel = ({
  detail,
  isLoading = false,
  onEdit,
}: AnalysisResultPanelProps) => {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div
        className="rounded-lg border border-border-color bg-white p-6 text-sm text-brand-text-sub dark:bg-brand-primary"
        data-testid="analysis-result-preview-loading"
      >
        {t("AnalysisResultPreview.Loading")}
      </div>
    );
  }

  if (!detail) {
    return (
      <div
        className="rounded-lg border border-dashed border-border-color bg-white p-6 text-sm text-brand-text-sub dark:bg-brand-primary"
        data-testid="analysis-result-preview-empty"
      >
        {t("AnalysisResultPreview.Empty")}
      </div>
    );
  }

  return (
    <div
      className="flex flex-col flex-1 min-h-0"
      data-testid="analysis-result-preview"
    >
      {/* ヘッダー: 結果名 + 編集ボタン */}
      <div className="flex items-start justify-between gap-2 px-1 pb-2 shrink-0">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
            {detail.name}
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {detail.resultType} / {detail.tableName}
          </p>
        </div>
        {onEdit && (
          <button
            type="button"
            onClick={onEdit}
            className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-gray-500 hover:text-brand-primary hover:bg-brand-primary/10 transition-colors shrink-0"
            data-testid="edit-analysis-result-button"
            aria-label={t("EditAnalysisResultDialog.Title")}
          >
            <Pencil className="w-3.5 h-3.5" />
            {t("EditAnalysisResultDialog.EditButtonLabel")}
          </button>
        )}
      </div>

      {/* 結果コンテンツ */}
      <div className="app-scrollbar flex-1 overflow-y-auto min-h-0 pb-2">
        {detail.resultType === "regression" && (
          <RegressionResult result={toRegressionResult(detail)} />
        )}

        {detail.resultType === "confidence_interval" && (
          <ConfidenceIntervalResult
            result={toConfidenceIntervalResult(detail)}
          />
        )}

        {detail.resultType === "descriptive_statistics" && (
          <DescriptiveStatisticsResult
            resultId={detail.id}
            tableName={detail.tableName}
            statistics={detail.resultData.statistics as StatisticsMap}
          />
        )}

        {![
          "regression",
          "confidence_interval",
          "descriptive_statistics",
        ].includes(detail.resultType) && (
          <div
            className="rounded-lg border border-border-color bg-white p-6 text-sm text-brand-text-sub dark:bg-brand-primary"
            data-testid="analysis-result-preview-unsupported"
          >
            {t("AnalysisResultPreview.Unsupported", {
              resultType: detail.resultType,
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export const AnalysisResultPreview = () => {
  const { t } = useTranslation();
  const detail = useAnalysisResultsStore((state) => state.activeResultDetail);
  const isDetailLoading = useAnalysisResultsStore(
    (state) => state.isDetailLoading,
  );

  return (
    <PageLayout
      title={detail?.name ?? t("AnalysisResultPreview.Title")}
      description={
        detail
          ? `${detail.resultType} / ${detail.tableName}`
          : t("AnalysisResultPreview.Empty")
      }
    >
      <AnalysisResultPanel detail={detail} isLoading={isDetailLoading} />
    </PageLayout>
  );
};
