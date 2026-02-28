import { type ReactNode } from "react";
import { cn } from "../../lib/utils/helpers";

interface PageLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

export const PageLayout = ({
  children,
  title,
  description,
  className,
}: PageLayoutProps) => {
  return (
    <div className={cn("w-full h-full flex flex-col px-3", className)}>
      {title && description ? (
        <div className="flex flex-1 flex-col gap-2 min-h-0">
          <header className="shrink-0">
            <h1 className="text-xl font-bold text-black">{title}</h1>
            <p className="mt-1 text-xs text-black/60">{description}</p>
          </header>
          {children}
        </div>
      ) : (
        children
      )}
    </div>
  );
};
