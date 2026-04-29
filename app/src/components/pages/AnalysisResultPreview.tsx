import type { AnalysisResultDetail } from "@/api/model";
import { PageLayout } from "@/components/templates/PageLayout";
import { ConfidenceIntervalResult } from "@/components/organisms/Result/ConfidenceIntervalResult";
import { DescriptiveStatisticsResult } from "@/components/organisms/Result/DescriptiveStatisticsResult";
import { RegressionResult } from "@/components/organisms/Result/RegressionResult";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import type { ConfidenceIntervalResultEntry } from "@/stores/confidenceIntervalResults";
import { useTranslation } from "react-i18next";
import type { LinearRegressionResultType } from "@/types/commonTypes";

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
};

export const AnalysisResultPanel = ({
  detail,
  isLoading = false,
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
      className="flex-1 overflow-y-auto min-h-0 pb-2"
      data-testid="analysis-result-preview"
    >
      {detail.resultType === "regression" && (
        <RegressionResult result={toRegressionResult(detail)} />
      )}

      {detail.resultType === "confidence_interval" && (
        <ConfidenceIntervalResult result={toConfidenceIntervalResult(detail)} />
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
