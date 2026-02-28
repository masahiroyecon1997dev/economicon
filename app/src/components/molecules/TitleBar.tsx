import { getCurrentWindow } from "@tauri-apps/api/window";
import { Minus, Square, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { cn } from "../../lib/utils/helpers";

/**
 * カスタムタイトルバー
 *
 * Tauri の decorations:false によって OS ネイティブのタイトルバーが
 * 無効化された場合に使用するカスタム実装。
 * - `data-tauri-drag-region` でウィンドウドラッグを実現
 * - ボタン要素には `data-tauri-drag-region` を付与しない（クリック阻害防止）
 */
export const TitleBar = () => {
  const [isMaximized, setIsMaximized] = useState(false);

  // 最大化状態を購読して □ / ❐ アイコンを切り替える
  useEffect(() => {
    const appWindow = getCurrentWindow();
    let unlistenFn: (() => void) | undefined;

    appWindow.isMaximized().then(setIsMaximized);

    appWindow
      .onResized(async () => {
        const maximized = await appWindow.isMaximized();
        setIsMaximized(maximized);
      })
      .then((fn) => {
        unlistenFn = fn;
      });

    return () => {
      unlistenFn?.();
    };
  }, []);

  const handleMinimize = useCallback(async () => {
    await getCurrentWindow().minimize();
  }, []);

  const handleToggleMaximize = useCallback(async () => {
    await getCurrentWindow().toggleMaximize();
  }, []);

  const handleClose = useCallback(async () => {
    await getCurrentWindow().close();
  }, []);

  return (
    // ドラッグ領域：バー全体。ボタンは除外される（pointer-events は子要素でリセット可能）
    <div
      data-tauri-drag-region
      className="flex h-8 shrink-0 select-none items-center justify-between bg-brand-primary-dark"
    >
      {/* アプリ名ラベル：ドラッグ領域の一部。クリックイベント不要なため pointer-events-none */}
      <span
        data-tauri-drag-region
        className="pointer-events-none pl-3 text-xs font-semibold tracking-widest text-white/50"
      >
        ECONOMICON
      </span>

      {/* ウィンドウ制御ボタン群：ドラッグ領域を外す（data-tauri-drag-region は付与しない） */}
      <div className="flex h-full">
        {/* 最小化 */}
        <button
          type="button"
          onClick={handleMinimize}
          aria-label="最小化"
          className={cn(
            "flex h-full w-12 items-center justify-center",
            "text-white/60 transition-colors",
            "hover:bg-white/10 hover:text-white",
            "focus:outline-none",
          )}
        >
          <Minus size={14} strokeWidth={1.5} />
        </button>

        {/* 最大化 / 元のサイズに戻す */}
        <button
          type="button"
          onClick={handleToggleMaximize}
          aria-label={isMaximized ? "元のサイズに戻す" : "最大化"}
          className={cn(
            "flex h-full w-12 items-center justify-center",
            "text-white/60 transition-colors",
            "hover:bg-white/10 hover:text-white",
            "focus:outline-none",
          )}
        >
          {isMaximized ? (
            // ❐ 元のサイズに戻す: 重なった二重矩形で表現
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
            <Square size={14} strokeWidth={1.5} />
          )}
        </button>

        {/* 閉じる: ホバー時に赤背景（Windows 標準スタイル） */}
        <button
          type="button"
          onClick={handleClose}
          aria-label="閉じる"
          className={cn(
            "flex h-full w-12 items-center justify-center",
            "text-white/60 transition-colors",
            "hover:bg-red-600 hover:text-white",
            "focus:outline-none",
          )}
        >
          <X size={14} strokeWidth={1.5} />
        </button>
      </div>
    </div>
  );
};
