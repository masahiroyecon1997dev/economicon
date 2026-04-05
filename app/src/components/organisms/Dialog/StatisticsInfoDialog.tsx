/**
 * StatisticsInfoDialog
 *
 * 統計量タイプの学術的説明を表示する汎用情報ダイアログ。
 * statisticKey に対応する i18n キー `StatisticsInfo.[statisticKey].*` を使用する。
 * 将来的には他の分析（統計的検定など）でも category を追加して再利用できる設計。
 */
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { useTranslation } from "react-i18next";

export type StatisticsInfoCategory = "confidence_interval";

export type StatisticsInfoDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** 統計量のキー（例: "proportion", "mean"）。i18n の StatisticsInfo.[key].* に対応 */
  statisticKey: string;
  /** 分析カテゴリ（将来拡張用）。現在は "confidence_interval" のみ */
  category?: StatisticsInfoCategory;
};

export const StatisticsInfoDialog = ({
  open,
  onOpenChange,
  statisticKey,
}: StatisticsInfoDialogProps) => {
  const { t } = useTranslation();

  const titleKey = `StatisticsInfo.${statisticKey}.Title`;
  const descKey = `StatisticsInfo.${statisticKey}.Description`;
  const formulaKey = `StatisticsInfo.${statisticKey}.Formula`;
  const assumptionsKey = `StatisticsInfo.${statisticKey}.Assumptions`;

  const title = t(titleKey);
  const description = t(descKey);
  const formula = t(formulaKey);
  const assumptions = t(assumptionsKey);

  // i18n フォールバック: キーがそのまま返ってきた場合は非表示
  const hasFormula = formula !== formulaKey;
  const hasAssumptions = assumptions !== assumptionsKey;

  return (
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      maxWidth="md"
      footerVariant="ok"
      onSubmit={() => onOpenChange(false)}
      data-testid="statistics-info-dialog"
    >
      <div className="space-y-4 text-sm text-gray-700">
        {/* 説明 */}
        <p className="leading-relaxed">{description}</p>

        {/* 計算式 */}
        {hasFormula && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              {t("StatisticsInfo.FormulaLabel")}
            </h4>
            <div className="bg-gray-50 border border-gray-200 rounded-md px-4 py-2.5 font-mono text-xs leading-relaxed whitespace-pre-wrap">
              {formula}
            </div>
          </div>
        )}

        {/* 前提条件 */}
        {hasAssumptions && (
          <div>
            <h4 className="font-semibold text-gray-800 mb-1">
              {t("StatisticsInfo.AssumptionsLabel")}
            </h4>
            <p className="leading-relaxed text-gray-600">{assumptions}</p>
          </div>
        )}
      </div>
    </BaseDialog>
  );
};
