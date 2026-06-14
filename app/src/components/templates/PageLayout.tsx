import { cn } from "@/lib/utils/helpers";
import { type ReactNode } from "react";

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
  /** タイトルの右に配置する追加要素（? ボタンなど） */
  titleAction?: ReactNode;
  className?: string;
}

export const PageLayout = ({
  children,
  title,
  description,
  titleAction,
  className,
}: PageLayoutProps) => {
  return (
    <div className={cn("w-full h-full flex flex-col px-3", className)}>
      {title && description ? (
        <div className="flex flex-1 flex-col gap-2 min-h-0">
          <header className="shrink-0">
            <div className="flex items-center gap-1.5 pt-2">
              <h1 className="text-xl font-bold text-black dark:text-gray-100">
                {title}
              </h1>
              {titleAction}
            </div>
            <p className="mt-1 text-xs text-black/60 dark:text-gray-400">
              {description}
            </p>
          </header>
          {children}
        </div>
      ) : (
        children
      )}
    </div>
  );
};
