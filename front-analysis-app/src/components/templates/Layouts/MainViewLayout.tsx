import { type ReactNode } from "react";

interface MainViewLayoutProps {
  children: ReactNode;
  maxWidth?: "none" | "4xl" | "6xl";
  includeHeight?: boolean;
  title?: string;
  description?: string;
}

export const MainViewLayout = ({
  children,
  maxWidth = "none",
  includeHeight = false,
  title,
  description
}: MainViewLayoutProps) => {
  const maxWidthClass = maxWidth === "none"
    ? "max-w-none"
    : maxWidth === "4xl"
      ? "max-w-4xl"
      : "max-w-6xl";

  const heightClass = includeHeight ? "h-full" : "";

  return (
    <div className={`mx-auto w-full ${maxWidthClass} px-3 ${heightClass}`}>
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
