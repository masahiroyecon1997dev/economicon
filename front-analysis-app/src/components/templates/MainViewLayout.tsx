import { type ReactNode } from "react";
import { ViewHeader } from "../molecules/Header/ViewHeader";

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
          <ViewHeader title={title} description={description} />
          {children}
        </div>
      ) : (
        children
      )}
    </div>
  );
};
