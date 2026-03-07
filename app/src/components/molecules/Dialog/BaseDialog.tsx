/**
 * 共通ダイアログシェル
 *
 * - Radix Dialog でモーダル表示
 * - ヘッダー: タイトル + 任意サブタイトル + 閉じるボタン（新スタイル統一）
 * - フッター: "ok" / "confirm" / "none" の3種類
 *   - "ok"      → OKボタン（MessageDialog 用）
 *   - "confirm" → キャンセル + 送信ボタン（操作ダイアログ用）
 *   - "none"    → フッターなし
 * - submitFormId を指定すると HTML5 フォーム関連付けで送信
 * - ダークモード完全対応
 */
import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import { Button } from "../../atoms/Button/Button";

// ─── 型定義 ──────────────────────────────────────────────────────────────────

const MAX_WIDTH_MAP = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
} as const;

export type BaseDialogPropsType = {
  open: boolean;
  onOpenChange: (open: boolean) => void;

  // ── ヘッダー ──────────────────────────────────────────────────────────
  title: string;
  /** 列名・テーブル名・ファイルパスなどのサブテキスト */
  subtitle?: string;

  // ── サイズ ────────────────────────────────────────────────────────────
  maxWidth?: keyof typeof MAX_WIDTH_MAP;

  // ── フッター ──────────────────────────────────────────────────────────
  /**
   * "ok"      → OKボタンのみ
   * "confirm" → キャンセル + 送信ボタン
   * "none"    → フッターなし
   */
  footerVariant: "ok" | "confirm" | "none";
  /** 送信ボタンのラベル。デフォルト: t("Common.OK") */
  submitLabel?: string;
  /**
   * HTML5 フォーム関連付け用 ID。
   * 指定すると送信ボタンが type="submit" form="{submitFormId}" になる。
   */
  submitFormId?: string;
  /** submitFormId を使わない場合の直接コールバック */
  onSubmit?: () => void;
  /** 送信中フラグ（ボタン disabled + "..." 表示） */
  isSubmitting?: boolean;
  /** isDirty チェックなど追加の無効化条件 */
  isSubmitDisabled?: boolean;
  /**
   * 送信ボタンのスタイル。デフォルト: "primary"
   * 削除など破壊的操作には "danger" を指定する。
   */
  submitVariant?: "primary" | "danger";

  children: ReactNode;
  /** Dialog.Content に追加するクラス名 */
  className?: string;
  /** コンテンツ領域のクラス名。デフォルト: "px-5 py-4" */
  contentClassName?: string;
};

// ─── BaseDialog ──────────────────────────────────────────────────────────────

export const BaseDialog = ({
  open,
  onOpenChange,
  title,
  subtitle,
  maxWidth = "md",
  footerVariant,
  submitLabel,
  submitFormId,
  onSubmit,
  isSubmitting = false,
  isSubmitDisabled = false,
  submitVariant = "primary",
  children,
  className,
  contentClassName,
}: BaseDialogPropsType) => {
  const { t } = useTranslation();

  const resolvedSubmitLabel =
    submitLabel ?? (footerVariant === "ok" ? t("Common.OK") : t("Common.OK"));

  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-gray-900/40" />
        <RadixDialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-full -translate-x-1/2 -translate-y-1/2",
            "overflow-hidden rounded-xl bg-white dark:bg-gray-900 shadow-xl",
            MAX_WIDTH_MAP[maxWidth],
            className,
          )}
          aria-describedby={undefined}
        >
          {/* ── ヘッダー ── */}
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-4">
            <div className="min-w-0 flex-1 pr-3">
              <RadixDialog.Title className="text-base font-semibold text-gray-900 dark:text-gray-100">
                {title}
              </RadixDialog.Title>
              {subtitle && (
                <p className="mt-0.5 truncate font-mono text-xs text-gray-500 dark:text-gray-400">
                  {subtitle}
                </p>
              )}
            </div>
            <RadixDialog.Close asChild>
              <button
                type="button"
                className="rounded-lg p-1.5 text-gray-400 dark:text-gray-500 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
                aria-label={t("Common.Close")}
              >
                <X className="h-4 w-4" />
              </button>
            </RadixDialog.Close>
          </div>

          {/* ── コンテンツ ── */}
          <div className={cn("px-5 py-4 dark:text-gray-200", contentClassName)}>
            {children}
          </div>

          {/* ── フッター ── */}
          {footerVariant !== "none" && (
            <div className="flex items-center justify-end gap-2 border-t border-gray-100 dark:border-gray-700 px-5 py-3">
              {footerVariant === "confirm" && (
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={isSubmitting}
                >
                  {t("Common.Cancel")}
                </Button>
              )}
              <Button
                variant={submitVariant}
                type={submitFormId ? "submit" : "button"}
                form={submitFormId}
                onClick={!submitFormId ? onSubmit : undefined}
                disabled={isSubmitting || isSubmitDisabled}
              >
                {isSubmitting ? "..." : resolvedSubmitLabel}
              </Button>
            </div>
          )}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};
