import {
  ResultSection,
  StatItem,
} from "@/components/molecules/Result/ResultSection";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import { useTranslation } from "react-i18next";

type TobitDiagnosticsProps = {
  diagnostics: NonNullable<LinearRegressionResultType["diagnostics"]>;
  formatNumber: (num: number | null | undefined, decimals?: number) => string;
};

export const TobitDiagnostics = ({
  diagnostics,
  formatNumber,
}: TobitDiagnosticsProps) => {
  const { t } = useTranslation();
  const { censoringLimits, sigma, waldTest, lrTest } = diagnostics;

  return (
    <ResultSection title={t("TobitDiagnostics.Title")}>
      <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
        {/* Sigma */}
        <StatItem label="σ (Sigma)" value={formatNumber(sigma)} />

        {/* 打ち切り値 */}
        {censoringLimits && (
          <>
            <StatItem
              label={t("TobitDiagnostics.LeftCensoringLimit")}
              value={
                censoringLimits.left !== null &&
                censoringLimits.left !== undefined
                  ? formatNumber(censoringLimits.left)
                  : t("RegressionResult.NA")
              }
            />
            <StatItem
              label={t("TobitDiagnostics.RightCensoringLimit")}
              value={
                censoringLimits.right !== null &&
                censoringLimits.right !== undefined
                  ? formatNumber(censoringLimits.right)
                  : t("RegressionResult.NA")
              }
            />
          </>
        )}
      </div>

      {/* LR検定 */}
      {lrTest && (
        <div className="mt-3">
          <h4 className="mb-2 text-xs font-semibold text-text-heading">
            {t("TobitDiagnostics.LRTest")}
          </h4>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
            <StatItem
              label={t("TobitDiagnostics.TestStatistic")}
              value={formatNumber(lrTest.statistic)}
            />
            <StatItem
              label={t("TobitDiagnostics.PValue")}
              value={formatNumber(lrTest.pValue)}
            />
            <StatItem label={t("TobitDiagnostics.DF")} value={lrTest.df} />
          </div>
        </div>
      )}

      {/* Wald検定 */}
      {waldTest && (
        <div className="mt-3">
          <h4 className="mb-2 text-xs font-semibold text-text-heading">
            {t("TobitDiagnostics.WaldTest")}
          </h4>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
            <StatItem
              label={t("TobitDiagnostics.TestStatistic")}
              value={formatNumber(waldTest.statistic)}
            />
            <StatItem
              label={t("TobitDiagnostics.PValue")}
              value={formatNumber(waldTest.pValue)}
            />
            <StatItem label={t("TobitDiagnostics.DF")} value={waldTest.df} />
          </div>
        </div>
      )}
    </ResultSection>
  );
};
