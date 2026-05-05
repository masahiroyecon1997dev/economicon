import { cn } from "@/lib/utils/helpers";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

type AnalysisOptionsCardProps = {
  title: string;
  summary: ReactNode;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
};

export const AnalysisOptionsCard = ({
  title,
  summary,
  open,
  onToggle,
  children,
  className,
  contentClassName,
}: AnalysisOptionsCardProps) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-border-color bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800",
        className,
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between px-3 py-2.5 text-left transition-colors hover:bg-secondary/50 dark:hover:bg-gray-700/50"
      >
        <div className="flex flex-col gap-0.5">
          <span className="text-sm font-bold text-text-heading dark:text-gray-100">
            {title}
          </span>
          <span className="text-xs text-brand-text-main/60 dark:text-gray-400">
            {summary}
          </span>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-brand-text-main/60 transition-transform duration-200",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          className={cn(
            "border-t border-border-color px-3 pb-4 pt-3 dark:border-gray-700",
            contentClassName,
          )}
        >
          {children}
        </div>
      )}
    </div>
  );
};
