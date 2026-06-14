/**
 * ExplainerDialog
 *
 * 統計・計量経済学の概念を解説する汎用ダイアログ。
 * - Zustand store (useExplainerDialogStore) が保持するキーで表示内容を制御。
 * - 数式は react-katex の BlockMath で KaTeX レンダリング。
 * - コンテンツは src/i18n/explainer/{en,ja}.ts の型付き TS ファイルから取得。
 */
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { enExplainer } from "@/i18n/explainer/en";
import { jaExplainer } from "@/i18n/explainer/ja";
import { useExplainerDialogStore } from "@/stores/explainerDialog";
import "katex/dist/katex.min.css";
import { useTranslation } from "react-i18next";
import { BlockMath } from "react-katex";

const getContent = (lang: string, key: string) => {
  const map = lang === "ja" ? jaExplainer : enExplainer;
  return (
    (map as Record<string, (typeof enExplainer)[keyof typeof enExplainer]>)[
      key
    ] ?? null
  );
};

export const ExplainerDialog = () => {
  const { t, i18n } = useTranslation();
  const key = useExplainerDialogStore((s) => s.key);
  const close = useExplainerDialogStore((s) => s.close);

  const content = key ? getContent(i18n.language, key) : null;

  return (
    <BaseDialog
      open={key !== null}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      title={content?.title ?? ""}
      maxWidth="md"
      footerVariant="ok"
      onSubmit={close}
      data-testid="explainer-dialog"
    >
      {content && (
        <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
          {/* 説明本文 */}
          {content.description.split("\n\n").map((paragraph, i) => (
            <p key={i} className="leading-relaxed">
              {paragraph}
            </p>
          ))}

          {/* 数式 */}
          {content.formula && (
            <div>
              <h4 className="mb-1 font-semibold text-gray-800 dark:text-gray-100">
                {t("Explainer.FormulaLabel")}
              </h4>
              <div className="overflow-x-auto rounded-md border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/60">
                <BlockMath
                  math={content.formula}
                  renderError={(error) => (
                    <span className="font-mono text-xs text-red-500">
                      {error.message}
                    </span>
                  )}
                />
              </div>
            </div>
          )}

          {/* 前提条件 */}
          {content.assumptions && (
            <div>
              <h4 className="mb-1 font-semibold text-gray-800 dark:text-gray-100">
                {t("Explainer.AssumptionsLabel")}
              </h4>
              <p className="leading-relaxed text-gray-600 dark:text-gray-400">
                {content.assumptions}
              </p>
            </div>
          )}
        </div>
      )}
    </BaseDialog>
  );
};
