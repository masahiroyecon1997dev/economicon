import { type ReactNode } from "react";
import { cn } from "../../../functions/utils";

interface MainViewLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

export const MainViewLayout = ({
  children,
  title,
  description,
  className,
}: MainViewLayoutProps) => {

  return (
    <div className={cn("w-full h-full px-3", className)}>
      {title && description ? (
        <div className="flex flex-col gap-3 md:gap-6">
          <header className="shrink-0">
            <h1 className="text-xl md:text-2xl font-bold text-black">{title}</h1>
            <p className="mt-1 md:mt-2 text-xs md:text-sm text-black/60">{description}</p>
          </header>
          {children}
        </div>
      ) : (
        children
      )}
    </div>
  );
};
