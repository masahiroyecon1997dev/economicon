import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { cn } from "@/lib/utils/helpers";
import { Loader2 } from "lucide-react";
import type { RefObject } from "react";

type PlotPanelProps = {
  /** Plotly が描画する div への ref */
  plotRef: RefObject<HTMLDivElement | null>;
  loading: boolean;
  error: string | null;
  /** true のとき plot div を表示する（結果あり＆エラーなし） */
  hasData: boolean;
  /** ローディング中に表示するテキスト（省略時は非表示） */
  loadingText?: string;
  className?: string;
  /** 外側コンテナの data-testid */
  testId?: string;
  /** 内側 plot div の data-testid */
  plotTestId?: string;
};

export const PlotPanel = ({
  plotRef,
  loading,
  error,
  hasData,
  loadingText,
  className,
  testId,
  plotTestId,
}: PlotPanelProps) => {
  return (
    <div
      className={cn("relative flex items-center justify-center", className)}
      data-testid={testId}
    >
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-bg-base/60 z-10">
          <Loader2 className="h-6 w-6 animate-spin text-brand-accent" />
          {loadingText && (
            <span className="text-sm text-text-main/60">{loadingText}</span>
          )}
        </div>
      )}

      {error && !loading && (
        <div className="w-full max-w-sm">
          <ErrorAlert message={error} />
        </div>
      )}

      <div
        ref={plotRef}
        className={cn(
          "w-full h-full",
          (!hasData || !!error) && "hidden",
          loading && "opacity-30",
        )}
        data-testid={plotTestId}
      />
    </div>
  );
};
