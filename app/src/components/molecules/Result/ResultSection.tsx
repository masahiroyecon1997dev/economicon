import { cn } from "@/lib/utils/helpers";
import type { ReactNode } from "react";

// セクションカード（タイトル + コンテンツ）
type ResultSectionProps = {
  title: string;
  children: ReactNode;
  className?: string;
  /** タイトル右側に配置する追加要素（? ボタンなど） */
  titleAction?: ReactNode;
};

export const ResultSection = ({
  title,
  children,
  className,
  titleAction,
}: ResultSectionProps) => (
  <div
    className={cn(
      "rounded-xl border border-border-color bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800",
      className,
    )}
  >
    <div className="mb-3 flex items-center gap-1.5">
      <h3 className="text-base font-bold text-text-heading">{title}</h3>
      {titleAction}
    </div>
    {children}
  </div>
);

// 統計値セル（ラベル + 数値）
type StatItemProps = {
  label: string;
  value: string | number;
};

export const StatItem = ({ label, value }: StatItemProps) => (
  <div className="flex flex-col">
    <span className="text-xs text-brand-text-main/60">{label}</span>
    <span className="font-semibold text-brand-text-main">{value}</span>
  </div>
);

// 強調表示カード（R² など）
type HighlightStatCardProps = {
  label: string;
  value: string;
};

export const HighlightStatCard = ({ label, value }: HighlightStatCardProps) => (
  <div className="flex flex-col rounded-lg bg-brand-accent/5 p-3">
    <span className="text-xs font-medium text-brand-accent/70">{label}</span>
    <span className="mt-0.5 text-2xl font-bold text-brand-accent">{value}</span>
  </div>
);
