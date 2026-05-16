import { cn } from "@/lib/utils/helpers";
import type { ReactNode } from "react";

type SectionCardProps = {
  title?: string;
  description?: string;
  headerRight?: ReactNode;
  children: ReactNode;
  className?: string;
};

export const SectionCard = ({
  title,
  description,
  headerRight,
  children,
  className,
}: SectionCardProps) => (
  <div
    className={cn(
      "rounded-xl border border-border-color bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800",
      className,
    )}
  >
    {title && (
      <div
        className={cn(
          "mb-3",
          headerRight && "flex items-center justify-between",
        )}
      >
        <div>
          <h2 className="text-sm font-bold leading-tight text-text-heading">
            {title}
          </h2>
          {description && (
            <p className="mt-0.5 text-xs text-brand-text-main/60">
              {description}
            </p>
          )}
        </div>
        {headerRight}
      </div>
    )}
    {children}
  </div>
);
