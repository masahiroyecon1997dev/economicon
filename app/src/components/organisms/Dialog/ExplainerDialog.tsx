/**
 * ExplainerDialog
 *
 * 統計・計量経済学の概念を解説する汎用ダイアログ。
 * - Zustand store (useExplainerDialogStore) が保持するキー・triggerRect で制御。
 * - ダイアログは triggerRect の中心を origin にして zoom-in / zoom-out アニメーション。
 * - コンテンツは react-markdown + remark-math + rehype-katex で Markdown レンダリング。
 * - ダイアログ幅は ExplainerItem.size で制御（デフォルト: "md"）。
 * - コンテンツは src/i18n/explainer/{en,ja}.ts の型付き TS ファイルから取得。
 */
import { Button } from "@/components/atoms/Button/Button";
import { enExplainer } from "@/i18n/explainer/en";
import { jaExplainer } from "@/i18n/explainer/ja";
import type { ExplainerItem, ExplainerItemSize } from "@/i18n/explainer/types";
import { cn } from "@/lib/utils/helpers";
import { useExplainerDialogStore } from "@/stores/explainerDialog";
import * as RadixDialog from "@radix-ui/react-dialog";
import "katex/dist/katex.min.css";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

const getContent = (lang: string, key: string): ExplainerItem | null => {
  const map = lang === "ja" ? jaExplainer : enExplainer;
  return (map as Record<string, ExplainerItem>)[key] ?? null;
};

const sizeClass: Record<ExplainerItemSize, string> = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  "2xl": "max-w-[min(80vw,64rem)]",
};

/**
 * triggerRect の中心を基準にした CSS transform-origin を返す。
 * ダイアログは固定位置（viewport 中央）に配置されるため、
 * `calc(50% + offset)` 形式でダイアログ座標系に変換する。
 */
const resolveTransformOrigin = (triggerRect: DOMRect | null): string => {
  if (!triggerRect) return "50% 50%";
  const bx = triggerRect.left + triggerRect.width / 2;
  const by = triggerRect.top + triggerRect.height / 2;
  const cx = window.innerWidth / 2;
  const cy = window.innerHeight / 2;
  return `calc(50% + ${bx - cx}px) calc(50% + ${by - cy}px)`;
};

export const ExplainerDialog = () => {
  const { t, i18n } = useTranslation();
  const key = useExplainerDialogStore((s) => s.key);
  const triggerRect = useExplainerDialogStore((s) => s.triggerRect);
  const close = useExplainerDialogStore((s) => s.close);

  const content = key ? getContent(i18n.language, key) : null;
  const transformOrigin = resolveTransformOrigin(triggerRect);
  const maxWClass = sizeClass[content?.size ?? "md"];

  return (
    <RadixDialog.Root
      open={key !== null}
      onOpenChange={(open) => {
        if (!open) close();
      }}
    >
      <RadixDialog.Portal>
        {/* オーバーレイ: フェードのみ */}
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-gray-900/40 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 duration-200" />

        {/* コンテンツ: triggerRect から zoom */}
        <RadixDialog.Content
          style={{ transformOrigin }}
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-full -translate-x-1/2 -translate-y-1/2",
            "flex max-h-[calc(100svh-3rem)] flex-col overflow-hidden rounded-xl bg-white shadow-xl dark:bg-gray-900",
            maxWClass,
            // open: triggerRect から拡大
            "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-0",
            // close: triggerRect へ縮小
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-0",
            "duration-200",
          )}
          aria-describedby={undefined}
          data-testid="explainer-dialog"
        >
          {/* ヘッダー */}
          <div className="flex shrink-0 items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-700">
            <RadixDialog.Title className="min-w-0 flex-1 pr-3 text-base font-semibold text-gray-900 dark:text-gray-100">
              {content?.title ?? ""}
            </RadixDialog.Title>
            <RadixDialog.Close
              className="rounded-md p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
              aria-label={t("Common.Close")}
            >
              <X size={16} aria-hidden="true" />
            </RadixDialog.Close>
          </div>

          {/* スクロール可能なコンテンツ領域 */}
          {content && (
            <div className="app-scrollbar min-h-0 flex-1 overflow-y-auto px-5 py-4 text-sm text-gray-700 dark:text-gray-300">
              <ReactMarkdown
                remarkPlugins={[remarkMath, remarkGfm]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  p: ({ children }) => (
                    <p className="mb-3 leading-relaxed last:mb-0">{children}</p>
                  ),
                  h3: ({ children }) => (
                    <h3 className="mt-5 mb-2 border-b border-gray-200 pb-1 text-sm font-semibold text-gray-800 dark:border-gray-700 dark:text-gray-100">
                      {children}
                    </h3>
                  ),
                  h4: ({ children }) => (
                    <h4 className="mt-4 mb-1.5 font-semibold text-gray-800 dark:text-gray-100">
                      {children}
                    </h4>
                  ),
                  strong: ({ children }) => (
                    <strong className="font-semibold text-gray-800 dark:text-gray-100">
                      {children}
                    </strong>
                  ),
                  ul: ({ children }) => (
                    <ul className="mb-3 list-disc pl-5 leading-relaxed">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mb-3 list-decimal pl-5 leading-relaxed">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  table: ({ children }) => (
                    <div className="my-3 overflow-x-auto rounded-md border border-gray-200 dark:border-gray-700">
                      <table className="w-full text-sm">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      {children}
                    </thead>
                  ),
                  th: ({ children }) => (
                    <th className="px-3 py-2 text-left font-semibold text-gray-800 dark:text-gray-100">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border-t border-gray-200 px-3 py-2 dark:border-gray-700">
                      {children}
                    </td>
                  ),
                  code: ({ children }) => (
                    <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-xs dark:bg-gray-800">
                      {children}
                    </code>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="my-3 border-l-4 border-gray-300 pl-4 italic text-gray-600 dark:border-gray-600 dark:text-gray-400">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {content.body}
              </ReactMarkdown>
            </div>
          )}

          {/* フッター */}
          <div className="shrink-0 border-t border-gray-200 px-5 py-3 dark:border-gray-700">
            <div className="flex justify-end">
              <Button variant="primary" className="px-4 py-1.5" onClick={close}>
                {t("Common.OK")}
              </Button>
            </div>
          </div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};
