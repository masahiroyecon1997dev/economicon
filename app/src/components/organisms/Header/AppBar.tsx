import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  ChevronDown,
  HelpCircle,
  Layers,
  Minus,
  Square,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import { useCurrentPageStore } from "../../../stores/currentView";
import { useSettingsStore } from "../../../stores/settings";
import type { DropmenuPositionType } from "../../../types/commonTypes";
import { MenuItem } from "../../atoms/Menu/MenuItem";
import { DropdownMenu } from "../../molecules/Menu/DropdownMenu";

const MENU_POSITION: DropmenuPositionType = "bottom";

/**
 * 統合アプリバー
 *
 * TitleBar（ウィンドウ制御） + HeaderMenu（ナビゲーション）を1本に統合。
 * - `data-tauri-drag-region` をバー全体に付与し、ウィンドウドラッグを実現
 * - ボタン・メニュー等のインタラクティブ要素は data-tauri-drag-region を持たないため
 *   マウスダウン時に Tauri のドラッグ検出から外れ、正しくクリックされる
 * - osName が "macOS" の場合は左端にトラフィックライト、
 *   Windows / Linux は右端に Fluent スタイルのウィンドウ制御を表示
 */
export const AppBar = () => {
  const { t } = useTranslation();
  const osName = useSettingsStore((s) => s.osName);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const [isMaximized, setIsMaximized] = useState(false);
  const [isDataMenuOpen, setIsDataMenuOpen] = useState(false);
  const [isRegressionMenuOpen, setIsRegressionMenuOpen] = useState(false);

  const isMac = osName === "macOS";

  // 最大化状態を購読して □ / ❐ アイコンを切り替える
  useEffect(() => {
    const appWindow = getCurrentWindow();
    let unlisten: (() => void) | undefined;

    appWindow.isMaximized().then(setIsMaximized);

    appWindow
      .onResized(async () => {
        setIsMaximized(await appWindow.isMaximized());
      })
      .then((fn) => {
        unlisten = fn;
      });

    return () => {
      unlisten?.();
    };
  }, []);

  const handleMinimize = useCallback(() => getCurrentWindow().minimize(), []);
  const handleToggleMaximize = useCallback(
    () => getCurrentWindow().toggleMaximize(),
    [],
  );
  const handleClose = useCallback(() => getCurrentWindow().close(), []);

  // ダブルクリックで最大化トグル（ドラッグ領域上でのみ有効）
  const handleDragAreaDoubleClick = useCallback(() => {
    getCurrentWindow().toggleMaximize();
  }, []);

  const dataMenuItems = [
    {
      id: "data-generation",
      label: t("HeaderMenu.DataGeneration"),
      handleSelect: () => setCurrentView("CreateSimulationDataTable"),
    },
    {
      id: "calculate",
      label: t("HeaderMenu.Calculate"),
      handleSelect: () => setCurrentView("CalculationView"),
    },
  ];
  const regressionMenuItems = [
    {
      id: "linear-regression",
      label: t("HeaderMenu.LinearRegression"),
      handleSelect: () => setCurrentView("LinearRegressionForm"),
    },
  ];
  const menus = [
    {
      menuName: t("HeaderMenu.Data"),
      isOpen: isDataMenuOpen,
      onClose: () => setIsDataMenuOpen(false),
      items: dataMenuItems,
    },
    {
      menuName: t("HeaderMenu.Model"),
      isOpen: isRegressionMenuOpen,
      onClose: () => setIsRegressionMenuOpen(false),
      items: regressionMenuItems,
    },
  ];

  return (
    // data-tauri-drag-region をバー全体に設定。
    // Tauri は mousedown イベントのターゲットを確認し、
    // ボタン・input・select などの要素ではドラッグを開始しない。
    <header
      data-tauri-drag-region
      onDoubleClick={handleDragAreaDoubleClick}
      className="flex h-11 shrink-0 select-none items-center border-b border-brand-primary-dark bg-brand-primary text-white"
    >
      {/* ===== macOS: 左端トラフィックライト ===== */}
      {isMac && (
        <div className="flex items-center gap-1.5 pl-4 pr-3">
          {/* 閉じる（赤） */}
          <button
            type="button"
            onClick={handleClose}
            aria-label="閉じる"
            className={cn(
              "size-3 rounded-full bg-red-500",
              "hover:bg-red-400 transition-colors focus:outline-none",
            )}
          />
          {/* 最小化（黄） */}
          <button
            type="button"
            onClick={handleMinimize}
            aria-label="最小化"
            className={cn(
              "size-3 rounded-full bg-yellow-400",
              "hover:bg-yellow-300 transition-colors focus:outline-none",
            )}
          />
          {/* 最大化（緑） */}
          <button
            type="button"
            onClick={handleToggleMaximize}
            aria-label={isMaximized ? "元のサイズに戻す" : "最大化"}
            className={cn(
              "size-3 rounded-full bg-green-500",
              "hover:bg-green-400 transition-colors focus:outline-none",
            )}
          />
        </div>
      )}

      {/* ===== ロゴ + アプリ名（ドラッグ領域の視覚的な起点） ===== */}
      {/* pointer-events-none でクリックを透過させてドラッグ領域として機能させる */}
      <div
        data-tauri-drag-region
        className={cn(
          "pointer-events-none flex items-center gap-2",
          isMac ? "pl-2 pr-6" : "pl-5 pr-6",
        )}
      >
        <Layers size={18} className="text-white/80" aria-hidden="true" />
        <span className="text-sm font-bold tracking-wide">Economicon</span>
      </div>

      {/* ===== ナビゲーションメニュー ===== */}
      <nav className="flex items-center gap-0.5">
        {menus.map((menu) => (
          <div key={menu.menuName} className="relative">
            <DropdownMenu
              isOpen={menu.isOpen}
              onClose={menu.onClose}
              position={MENU_POSITION}
              triggerElement={
                <button
                  type="button"
                  className={cn(
                    "flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium",
                    "text-white/80 hover:bg-white/10 hover:text-white transition-colors",
                    "focus:outline-none",
                  )}
                >
                  <span>{menu.menuName}</span>
                  <ChevronDown size={14} aria-hidden="true" />
                </button>
              }
            >
              {menu.items.map((item, i) => (
                <MenuItem
                  key={item.id}
                  label={item.label}
                  variant="default"
                  isFirst={i === 0}
                  isLast={i === menu.items.length - 1}
                  handleSelect={item.handleSelect}
                />
              ))}
            </DropdownMenu>
          </div>
        ))}
      </nav>

      {/* ===== 右端: ヘルプ + Windows/Linux ウィンドウ制御 ===== */}
      <div className="ml-auto flex h-full items-center">
        <button
          type="button"
          aria-label="ヘルプ"
          className={cn(
            "rounded-full p-2",
            "text-white/60 hover:bg-white/10 hover:text-white transition-colors",
            "focus:outline-none",
          )}
        >
          <HelpCircle size={18} aria-hidden="true" />
        </button>

        {/* Windows / Linux のみ: 右端ウィンドウ制御ボタン */}
        {!isMac && (
          <div className="ml-1 flex h-full">
            {/* 最小化 */}
            <button
              type="button"
              onClick={handleMinimize}
              aria-label="最小化"
              className={cn(
                "flex h-full w-11 items-center justify-center",
                "text-white/60 hover:bg-white/10 hover:text-white transition-colors",
                "focus:outline-none",
              )}
            >
              <Minus size={14} strokeWidth={1.5} aria-hidden="true" />
            </button>

            {/* 最大化 / 元のサイズに戻す */}
            <button
              type="button"
              onClick={handleToggleMaximize}
              aria-label={isMaximized ? "元のサイズに戻す" : "最大化"}
              className={cn(
                "flex h-full w-11 items-center justify-center",
                "text-white/60 hover:bg-white/10 hover:text-white transition-colors",
                "focus:outline-none",
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
              onClick={handleClose}
              aria-label="閉じる"
              className={cn(
                "flex h-full w-11 items-center justify-center",
                "text-white/60 hover:bg-red-600 hover:text-white transition-colors",
                "focus:outline-none",
              )}
            >
              <X size={14} strokeWidth={1.5} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
