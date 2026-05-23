import type { AnimationSpeed } from "@/hooks/useSimulationAnimation";
import { cn } from "@/lib/utils/helpers";
import { Pause, Play, RotateCcw } from "lucide-react";
import { useTranslation } from "react-i18next";

type AnimationControlsProps = {
  playing: boolean;
  /** true のとき再生ボタンを有効にする（シミュレーション結果取得済みか） */
  canPlay: boolean;
  frame: number;
  total: number;
  speed: AnimationSpeed;
  onPlay: () => void;
  onPause: () => void;
  onReset: () => void;
  onSpeedChange: (speed: AnimationSpeed) => void;
  /** フレームカウンター表示テキストを上書きする場合に指定 */
  counterLabel?: string;
};

const SPEED_OPTIONS: AnimationSpeed[] = ["slow", "normal", "fast"];

export const AnimationControls = ({
  playing,
  canPlay,
  frame,
  total,
  speed,
  onPlay,
  onPause,
  onReset,
  onSpeedChange,
  counterLabel,
}: AnimationControlsProps) => {
  const { t } = useTranslation();

  const speedLabelKey = {
    slow: "AnimationControls.SpeedSlow",
    normal: "AnimationControls.SpeedNormal",
    fast: "AnimationControls.SpeedFast",
  } as const;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* 再生 / 一時停止トグル */}
      {playing ? (
        <button
          type="button"
          className="flex items-center gap-1 px-2 py-1 rounded text-sm bg-secondary hover:bg-secondary/70 transition-colors"
          onClick={onPause}
          data-testid="animation-pause-btn"
        >
          <Pause className="h-3.5 w-3.5" />
          {t("AnimationControls.Pause")}
        </button>
      ) : (
        <button
          type="button"
          className="flex items-center gap-1 px-2 py-1 rounded text-sm bg-secondary hover:bg-secondary/70 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          onClick={onPlay}
          disabled={!canPlay}
          data-testid="animation-play-btn"
        >
          <Play className="h-3.5 w-3.5" />
          {t("AnimationControls.Play")}
        </button>
      )}

      {/* リセット */}
      <button
        type="button"
        className="flex items-center gap-1 px-2 py-1 rounded text-sm bg-secondary hover:bg-secondary/70 transition-colors"
        onClick={onReset}
        data-testid="animation-reset-btn"
      >
        <RotateCcw className="h-3.5 w-3.5" />
        {t("AnimationControls.Reset")}
      </button>

      <div className="w-px h-4 bg-border-color mx-1" />

      {/* 速度セレクター */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-text-main/50">
          {t("AnimationControls.SpeedLabel")}
        </span>
        {SPEED_OPTIONS.map((s) => (
          <button
            key={s}
            type="button"
            className={cn(
              "px-2 py-0.5 rounded text-xs transition-colors",
              speed === s
                ? "bg-brand-accent text-white"
                : "bg-secondary hover:bg-secondary/70 text-text-main/70",
            )}
            onClick={() => onSpeedChange(s)}
            data-testid={`animation-speed-${s}`}
          >
            {t(speedLabelKey[s])}
          </button>
        ))}
      </div>

      {/* フレームカウンター */}
      <span
        className="text-xs font-mono text-text-main/60 ml-auto"
        data-testid="animation-counter"
      >
        {counterLabel ?? `${frame} / ${total}`}
      </span>
    </div>
  );
};
