import { Minus, Square, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";

type WindowControlsProps = {
  isMac: boolean;
  isMaximized: boolean;
  onMinimize: () => void;
  onToggleMaximize: () => void;
  onClose: () => void;
};

/** ウィンドウ制御ボタンに共通するクラス（cursor-default を強制） */
const WIN_CTRL_BTN = "cursor-default focus:outline-none transition-colors";

export const WindowControls = ({
  isMac,
  isMaximized,
  onMinimize,
  onToggleMaximize,
  onClose,
}: WindowControlsProps) => {
  const { t } = useTranslation();

  if (isMac) {
    return (
      <div className="flex items-center gap-1.5 pl-4 pr-3">
        {/* 閉じる（赤） */}
        <button
          type="button"
          onClick={onClose}
          aria-label={t("AppBar.Close")}
          className={cn(
            WIN_CTRL_BTN,
            "size-3 rounded-full bg-red-500 hover:bg-red-400",
          )}
        />
        {/* 最小化（黄） */}
        <button
          type="button"
          onClick={onMinimize}
          aria-label={t("AppBar.Minimize")}
          className={cn(
            WIN_CTRL_BTN,
            "size-3 rounded-full bg-yellow-400 hover:bg-yellow-300",
          )}
        />
        {/* 最大化（緑） */}
        <button
          type="button"
          onClick={onToggleMaximize}
          aria-label={isMaximized ? t("AppBar.Restore") : t("AppBar.Maximize")}
          className={cn(
            WIN_CTRL_BTN,
            "size-3 rounded-full bg-green-500 hover:bg-green-400",
          )}
        />
      </div>
    );
  }

  return (
    <div className="ml-1 flex h-full">
      {/* 最小化 */}
      <button
        type="button"
        onClick={onMinimize}
        aria-label={t("AppBar.Minimize")}
        className={cn(
          WIN_CTRL_BTN,
          "flex h-full w-11 items-center justify-center",
          "text-white/60 hover:bg-white/10 hover:text-white",
        )}
      >
        <Minus size={14} strokeWidth={1.5} aria-hidden="true" />
      </button>

      {/* 最大化 / 元のサイズに戻す */}
      <button
        type="button"
        onClick={onToggleMaximize}
        aria-label={isMaximized ? t("AppBar.Restore") : t("AppBar.Maximize")}
        className={cn(
          WIN_CTRL_BTN,
          "flex h-full w-11 items-center justify-center",
          "text-white/60 hover:bg-white/10 hover:text-white",
        )}
      >
        {isMaximized ? (
          // ❐ 二重矩形で「元に戻す」を表現
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <rect x="3" y="1" width="9" height="9" rx="0.5" />
            <path d="M1 4v8.5A0.5 0.5 0 001.5 13H10" />
          </svg>
        ) : (
          <Square size={14} strokeWidth={1.5} aria-hidden="true" />
        )}
      </button>

      {/* 閉じる: ホバー時に赤（Windows Fluent 標準） */}
      <button
        type="button"
        onClick={onClose}
        aria-label={t("AppBar.Close")}
        className={cn(
          WIN_CTRL_BTN,
          "flex h-full w-11 items-center justify-center",
          "text-white/60 hover:bg-red-600 hover:text-white",
        )}
      >
        <X size={14} strokeWidth={1.5} aria-hidden="true" />
      </button>
    </div>
  );
};
