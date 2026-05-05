import { ActionButtonBar } from "@/components/molecules/ActionBar/ActionButtonBar";
import { cn } from "@/lib/utils/helpers";
import { Database } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

type AnalysisEmptyStateActionProps = {
  cancelText?: string;
  onCancel?: () => void;
  selectText: string;
  onSelect: () => void;
  disabled?: boolean;
  isLoading?: boolean;
};

type AnalysisEmptyStateProps = {
  className?: string;
  testId?: string;
  icon: ReactNode;
  title: string;
  description: string;
  hint?: string;
  compact?: boolean;
  actions?: AnalysisEmptyStateActionProps;
};

type AnalysisNoTablesStateProps = {
  className?: string;
  testId?: string;
  onCancel?: () => void;
  onSelect?: () => void;
  cancelText?: string;
  selectText?: string;
};

export const AnalysisEmptyState = ({
  className,
  testId = "analysis-empty-state",
  icon,
  title,
  description,
  hint,
  compact = false,
  actions,
}: AnalysisEmptyStateProps) => {
  return (
    <div
      className={cn("flex min-h-0 flex-col gap-4", className)}
      data-testid={testId}
    >
      <div
        className={cn(
          "flex min-h-0 flex-col items-center justify-center rounded-xl border border-dashed border-border-color bg-white px-6 text-center dark:border-gray-700 dark:bg-gray-800",
          compact ? "py-6" : "flex-1 py-10",
        )}
      >
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-brand-secondary text-brand-text-sub dark:bg-gray-700 dark:text-gray-200">
          {icon}
        </div>
        <h2 className="text-base font-semibold text-brand-text-main dark:text-gray-100">
          {title}
        </h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-brand-text-sub dark:text-gray-400">
          {description}
        </p>
        {hint ? (
          <p className="mt-2 max-w-md text-xs leading-5 text-brand-text-sub/80 dark:text-gray-500">
            {hint}
          </p>
        ) : null}
      </div>

      {actions ? (
        <ActionButtonBar
          cancelText={actions.cancelText ?? ""}
          onCancel={actions.onCancel ?? (() => {})}
          selectText={actions.selectText}
          onSelect={actions.onSelect}
          disabled={actions.disabled}
          isLoading={actions.isLoading}
        />
      ) : null}
    </div>
  );
};

export const AnalysisNoTablesState = ({
  className,
  testId = "analysis-no-tables-state",
  onCancel,
  onSelect,
  cancelText,
  selectText,
}: AnalysisNoTablesStateProps) => {
  const { t } = useTranslation();

  return (
    <AnalysisEmptyState
      className={className}
      icon={<Database className="h-6 w-6" />}
      title={t("AnalysisEmptyState.NoTablesTitle")}
      description={t("AnalysisEmptyState.NoTablesDescription")}
      actions={
        onSelect
          ? {
              cancelText: cancelText ?? t("Common.Cancel"),
              onCancel,
              selectText:
                selectText ?? t("AnalysisEmptyState.NoTablesAction"),
              onSelect,
            }
          : undefined
      }
      testId={testId}
    />
  );
};