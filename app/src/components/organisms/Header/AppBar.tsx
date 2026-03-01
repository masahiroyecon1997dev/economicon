import { getCurrentWindow } from "@tauri-apps/api/window";
import {
  ChevronDown,
  Layers,
  Minus,
  MoreHorizontal,
  Settings,
  Square,
  X,
} from "lucide-react";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import { useCurrentPageStore } from "../../../stores/currentView";
import { useSettingsStore } from "../../../stores/settings";
import type { DropmenuPositionType } from "../../../types/commonTypes";
import { MenuItem } from "../../atoms/Menu/MenuItem";
import { DropdownMenu } from "../../molecules/Menu/DropdownMenu";
import { SettingsDialog } from "../Dialog/SettingsDialog";

const MENU_POSITION: DropmenuPositionType = "bottom-right";

/**
 * 統合アプリバー
 *
 * TitleBar（ウィンドウ制御） + HeaderMenu（ナビゲーション）を1本に統合。
 * - mousedown で起点を記録し、mousemove の閾値超えで startDragging() を呼び出す
 *   （mousedown 即呼び出しだと OS がマウスを捕捉して dblclick が届かなくなるため）
 * - ダブルクリックで最大化 ⇔ 復元をトグル（最大化中でも正しく動作）
 * - ボタン等のインタラクティブ要素上ではドラッグを開始しない
 * - osName が "macOS" の場合は左端にトラフィックライト、
 *   Windows / Linux は右端に Fluent スタイルのウィンドウ制御を表示
 */
export const AppBar = () => {
  const { t } = useTranslation();
  const osName = useSettingsStore((s) => s.osName);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const [isMaximized, setIsMaximized] = useState(false);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

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

  // マウスダウン起点を記録するref（startDragging は mousemove 時に初めて呼び出す）
  // 即 startDragging() するとOSがマウスを捕捉し dblclick イベントが届かなくなるため
  const mouseDownPosRef = useRef<{ x: number; y: number } | null>(null);

  // ナビゲーションオーバーフロー検出
  // navRef: 実際に表示される nav コンテナ（幅監視対象）
  // measureRef: 全メニューボタンを invisible で常時レンダリングし幅を計測する隠しコンテナ
  const navRef = useRef<HTMLDivElement>(null);
  const measureRef = useRef<HTMLDivElement>(null);
  const [visibleCount, setVisibleCount] = useState(999);

  useEffect(() => {
    const nav = navRef.current;
    const measure = measureRef.current;
    if (!nav || !measure) return;

    //「…」ボタン自身の幅（px）
    const OVERFLOW_BTN_W = 36;

    const recalculate = () => {
      const available = nav.clientWidth;
      const btns = Array.from(measure.children) as HTMLElement[];
      let total = 0;
      let count = 0;
      for (let i = 0; i < btns.length; i++) {
        const w = btns[i].getBoundingClientRect().width;
        const hasMore = i < btns.length - 1;
        if (hasMore) {
          // 次のアイテムが存在する:「…」ボタン分の幅を確保した上で収まるか判定
          if (total + w + OVERFLOW_BTN_W <= available) {
            total += w;
            count = i + 1;
          } else {
            break;
          }
        } else {
          // 最後のアイテム: 「…」ボタン不要なのでそのまま判定
          if (total + w <= available) {
            count = btns.length;
          }
        }
      }
      setVisibleCount(count);
    };

    recalculate();
    const ro = new ResizeObserver(recalculate);
    ro.observe(nav);
    return () => ro.disconnect();
  }, []);

  const handleMinimize = useCallback(() => getCurrentWindow().minimize(), []);
  const handleToggleMaximize = useCallback(
    () => getCurrentWindow().toggleMaximize(),
    [],
  );
  const handleClose = useCallback(() => getCurrentWindow().close(), []);

  /** ウィンドウ制御ボタンに共通するクラス（cursor-default を強制） */
  const WIN_CTRL_BTN = "cursor-default focus:outline-none transition-colors";

  // mousedown: 起点を記録するだけ。startDragging() はまだ呼ばない
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLElement>) => {
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    if (target.closest("button, a, input, select, textarea")) return;
    mouseDownPosRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  // mousemove: 4px 超の移動を検知して startDragging() を呼び出す
  // 最大化中でもそのまま呼び出し、OS がウィンドウを復元してから移動する
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLElement>) => {
    if (!mouseDownPosRef.current) return;
    const dx = Math.abs(e.clientX - mouseDownPosRef.current.x);
    const dy = Math.abs(e.clientY - mouseDownPosRef.current.y);
    if (dx > 4 || dy > 4) {
      mouseDownPosRef.current = null;
      getCurrentWindow().startDragging();
    }
  }, []);

  // mouseup: クリックで終わった場合はドラッグ意図をリセット
  const handleMouseUp = useCallback(() => {
    mouseDownPosRef.current = null;
  }, []);

  // ダブルクリック: ドラッグ意図をリセットした上で最大化トグル
  // 最大化中→復元、通常→最大化、どちらも正しく動作する
  const handleDoubleClick = useCallback((e: React.MouseEvent<HTMLElement>) => {
    const target = e.target as HTMLElement;
    if (target.closest("button, a, input, select, textarea")) return;
    mouseDownPosRef.current = null;
    getCurrentWindow().toggleMaximize();
  }, []);

  const close = () => setOpenMenuId(null);

  const menus = [
    {
      id: "file",
      menuName: t("HeaderMenu.File"),
      isOpen: openMenuId === "file",
      onClose: close,
      items: [
        {
          id: "import",
          label: t("HeaderMenu.ImportData"),
          handleSelect: () => {
            setCurrentView("ImportDataFile");
            close();
          },
        },
        {
          id: "save",
          label: t("HeaderMenu.SaveData"),
          handleSelect: () => {
            setCurrentView("SaveData");
            close();
          },
        },
      ],
    },
    {
      id: "table",
      menuName: t("HeaderMenu.Table"),
      isOpen: openMenuId === "table",
      onClose: close,
      items: [
        {
          id: "create-table",
          label: t("HeaderMenu.CreateTable"),
          handleSelect: () => {
            setCurrentView("CreateTable");
            close();
          },
        },
        {
          id: "join-table",
          label: t("HeaderMenu.JoinTable"),
          handleSelect: () => {},
        },
        {
          id: "union-table",
          label: t("HeaderMenu.UnionTable"),
          handleSelect: () => {},
        },
      ],
    },
    {
      id: "data",
      menuName: t("HeaderMenu.Data"),
      isOpen: openMenuId === "data",
      onClose: close,
      items: [
        {
          id: "data-generation",
          label: t("HeaderMenu.DataGeneration"),
          handleSelect: () => {
            setCurrentView("CreateSimulationDataTable");
            close();
          },
        },
        {
          id: "calculate",
          label: t("HeaderMenu.Calculate"),
          handleSelect: () => {
            setCurrentView("CalculationView");
            close();
          },
        },
        {
          id: "basic-statistics",
          label: t("HeaderMenu.BasicStatistics"),
          handleSelect: () => {},
        },
      ],
    },
    {
      id: "linear-regression",
      menuName: t("HeaderMenu.LinearRegressionMenu"),
      isOpen: openMenuId === "linear-regression",
      onClose: close,
      items: [
        {
          id: "linear-regression-item",
          label: t("HeaderMenu.LinearRegression"),
          handleSelect: () => {
            setCurrentView("LinearRegressionForm");
            close();
          },
        },
        // {
        //   id: "lasso-regression",
        //   label: t("HeaderMenu.LassoRegression"),
        //   handleSelect: () => {},
        // },
        // {
        //   id: "ridge-regression",
        //   label: t("HeaderMenu.RidgeRegression"),
        //   handleSelect: () => {},
        // },
      ],
    },
    // {
    //   id: "nonlinear-regression",
    //   menuName: t("HeaderMenu.NonlinearRegressionMenu"),
    //   isOpen: openMenuId === "nonlinear-regression",
    //   onClose: close,
    //   items: [
    //     {
    //       id: "logit",
    //       label: t("HeaderMenu.LogitAnalysis"),
    //       handleSelect: () => {},
    //     },
    //     {
    //       id: "probit",
    //       label: t("HeaderMenu.ProbitAnalysis"),
    //       handleSelect: () => {},
    //     },
    //     {
    //       id: "tobit",
    //       label: t("HeaderMenu.TobitAnalysis"),
    //       handleSelect: () => {},
    //     },
    //   ],
    // },
    // {
    //   id: "panel-data",
    //   menuName: t("HeaderMenu.PanelDataMenu"),
    //   isOpen: openMenuId === "panel-data",
    //   onClose: close,
    //   items: [
    //     {
    //       id: "fixed-effect",
    //       label: t("HeaderMenu.FixedEffect"),
    //       handleSelect: () => {},
    //     },
    //     {
    //       id: "random-effect",
    //       label: t("HeaderMenu.RandomEffect"),
    //       handleSelect: () => {},
    //     },
    //   ],
    // },
    // {
    //   id: "causal-inference",
    //   menuName: t("HeaderMenu.CausalInferenceMenu"),
    //   isOpen: openMenuId === "causal-inference",
    //   onClose: close,
    //   items: [
    //     {
    //       id: "instrumental-variables",
    //       label: t("HeaderMenu.InstrumentalVariables"),
    //       handleSelect: () => {},
    //     },
    //   ],
    // },
  ];

  return (
    // mousedown で起点を記録 → mousemove の移動量が閾値を超えた時点で startDragging()。
    // こうすることでダブルクリックイベントが正しく届き、最大化⇔復元が機能する。
    <header
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onDoubleClick={handleDoubleClick}
      className="relative flex h-11 shrink-0 select-none items-center border-b border-white/25 dark:border-gray-700 bg-brand-primary dark:bg-gray-900 text-white"
    >
      {/* ===== macOS: 左端トラフィックライト ===== */}
      {isMac && (
        <div className="flex items-center gap-1.5 pl-4 pr-3">
          {/* 閉じる（赤） */}
          <button
            type="button"
            onClick={handleClose}
            aria-label={t("AppBar.Close")}
            className={cn(
              WIN_CTRL_BTN,
              "size-3 rounded-full bg-red-500 hover:bg-red-400",
            )}
          />
          {/* 最小化（黄） */}
          <button
            type="button"
            onClick={handleMinimize}
            aria-label={t("AppBar.Minimize")}
            className={cn(
              WIN_CTRL_BTN,
              "size-3 rounded-full bg-yellow-400 hover:bg-yellow-300",
            )}
          />
          {/* 最大化（緑） */}
          <button
            type="button"
            onClick={handleToggleMaximize}
            aria-label={
              isMaximized ? t("AppBar.Restore") : t("AppBar.Maximize")
            }
            className={cn(
              WIN_CTRL_BTN,
              "size-3 rounded-full bg-green-500 hover:bg-green-400",
            )}
          />
        </div>
      )}

      {/* ===== ロゴ + アプリ名（ドラッグ領域の視覚的な起点） ===== */}
      {/* pointer-events-none でクリックを透過させてドラッグ領域として機能させる */}
      <div
        className={cn(
          "pointer-events-none flex items-center",
          isMac ? "pl-2 pr-4" : "pl-5 pr-4",
        )}
      >
        <Layers size={18} className="text-white/80" aria-hidden="true" />
      </div>

      {/* ===== ナビゲーションメニュー ===== */}

      {/*
       * 計測用の不可視コンテナ。
       * 全メニューボタンを visibility:hidden + pointer-events-none で常時レンダリングし、
       * ResizeObserver が各ボタンの実幅を測定するために使用する。
       * absolute 配置なのでレイアウトに影響しない。
       */}
      <div
        ref={measureRef}
        aria-hidden="true"
        className="invisible absolute flex pointer-events-none"
      >
        {menus.map((menu) => (
          <button
            key={menu.id}
            type="button"
            className="flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium"
          >
            <span>{menu.menuName}</span>
            <ChevronDown size={14} />
          </button>
        ))}
      </div>

      {/* 表示用 nav: flex-1 で利用可能幅を占有し、overflow-hidden で折り返しを防ぐ */}
      <nav
        ref={navRef}
        className="flex min-w-0 flex-1 items-center gap-0.5 overflow-hidden"
      >
        {/* 表示可能なメニュー */}
        {menus.slice(0, visibleCount).map((menu) => (
          <div key={menu.id} className="relative shrink-0">
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

        {/* オーバーフロー時の「…」ボタン */}
        {visibleCount < menus.length && (
          <div className="relative shrink-0">
            <DropdownMenu
              isOpen={openMenuId === "__overflow__"}
              onClose={close}
              position={MENU_POSITION}
              triggerElement={
                <button
                  type="button"
                  aria-label={t("AppBar.MoreMenus")}
                  className={cn(
                    "flex h-8 w-9 items-center justify-center rounded",
                    "text-white/80 hover:bg-white/10 hover:text-white transition-colors",
                    "focus:outline-none",
                  )}
                >
                  <MoreHorizontal size={16} aria-hidden="true" />
                </button>
              }
            >
              {menus.slice(visibleCount).map((menu, menuIdx) => (
                <Fragment key={menu.id}>
                  {/* グループ区切り線（最初のグループには不要）*/}
                  {menuIdx > 0 && (
                    <div className="my-1 border-t border-gray-100" />
                  )}
                  {/* グループ見出し */}
                  <div className="px-3 py-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
                    {menu.menuName}
                  </div>
                  {/* グループ内アイテム */}
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
                </Fragment>
              ))}
            </DropdownMenu>
          </div>
        )}
      </nav>

      {/* ===== 右端: 設定 + Windows/Linux ウィンドウ制御 ===== */}
      <div className="ml-auto flex h-full items-center">
        <button
          type="button"
          aria-label={t("AppBar.Settings")}
          onClick={() => setIsSettingsOpen(true)}
          className={cn(
            "rounded-full p-2",
            "text-white/60 hover:bg-white/10 hover:text-white transition-colors",
            "focus:outline-none",
          )}
        >
          <Settings size={18} aria-hidden="true" />
        </button>
        <SettingsDialog
          open={isSettingsOpen}
          onOpenChange={setIsSettingsOpen}
        />

        {/* Windows / Linux のみ: 右端ウィンドウ制御ボタン */}
        {!isMac && (
          <div className="ml-1 flex h-full">
            {/* 最小化 */}
            <button
              type="button"
              onClick={handleMinimize}
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
              onClick={handleToggleMaximize}
              aria-label={
                isMaximized ? t("AppBar.Restore") : t("AppBar.Maximize")
              }
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
              onClick={handleClose}
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
        )}
      </div>
    </header>
  );
};
