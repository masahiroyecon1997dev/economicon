/**
 * 設定ダイアログ（パターンA: タブ型サイドバーダイアログ）
 *
 * - Radix Dialog でモーダル表示
 * - Radix Tabs（vertical）で左サイドバー / 右コンテンツを構成
 * - 外観: テーマカード選択
 * - 一般: 言語・エンコーディング選択
 * - データ / ログ: 将来の拡張スペース
 * - 保存ボタンで PUT /api/settings を呼び出し、成功時に store を更新
 */
import * as Select from "@radix-ui/react-select";
import * as Tabs from "@radix-ui/react-tabs";
import {
  Check,
  ChevronDown,
  Database,
  FileText,
  Palette,
  SlidersHorizontal,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAPI } from "../../../api/endpoints";
import type { ThemeDefinitionType } from "../../../constants/themes";
import { THEMES } from "../../../constants/themes";
import { showMessageDialog } from "../../../lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../../lib/utils/apiError";
import { cn } from "../../../lib/utils/helpers";
import { useSettingsStore } from "../../../stores/settings";
import { BaseDialog } from "../../molecules/Dialog/BaseDialog";

// ─── 型定義 ──────────────────────────────────────────────────────────────────

export type SettingsDialogPropsType = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

type DraftSettingsType = {
  theme: string;
  language: string;
  encoding: string;
};

// ─── 定数 ────────────────────────────────────────────────────────────────────

const TABS = [
  {
    id: "appearance",
    labelKey: "SettingsDialog.Tabs.Appearance",
    Icon: Palette,
  },
  {
    id: "general",
    labelKey: "SettingsDialog.Tabs.General",
    Icon: SlidersHorizontal,
  },
  { id: "data", labelKey: "SettingsDialog.Tabs.Data", Icon: Database },
  { id: "log", labelKey: "SettingsDialog.Tabs.Log", Icon: FileText },
] as const;

const ENCODINGS = [
  "utf-8",
  "utf-8-sig",
  "shift-jis",
  "euc-jp",
  "cp932",
] as const;

const LANGUAGES = [
  { id: "ja", labelKey: "SettingsDialog.Language.Ja" },
  { id: "en", labelKey: "SettingsDialog.Language.En" },
] as const;

// ─── ThemeCard ───────────────────────────────────────────────────────────────

type ThemeCardPropsType = {
  theme: ThemeDefinitionType;
  isSelected: boolean;
  onClick: () => void;
};

const ThemeCard = ({ theme, isSelected, onClick }: ThemeCardPropsType) => {
  const { t } = useTranslation();
  const { preview } = theme;

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      className={cn(
        "flex flex-col overflow-hidden rounded-lg border-2 transition-all",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
        isSelected
          ? "border-blue-500 shadow-md"
          : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600",
      )}
    >
      {/* ミニUI プレビュー */}
      <div
        className="flex h-24 w-full overflow-hidden"
        style={{ background: preview.bg }}
        aria-hidden="true"
      >
        {/* 疑似サイドバー */}
        <div
          className="flex flex-col gap-1 p-2"
          style={{
            width: 48,
            background: preview.sidebar,
            borderRight: `1px solid ${preview.border}`,
          }}
        >
          <div
            className="rounded"
            style={{ height: 7, background: preview.accent, width: 30 }}
          />
          <div
            className="rounded"
            style={{ height: 4, background: preview.muted, width: 34 }}
          />
          <div
            className="rounded"
            style={{ height: 4, background: preview.muted, width: 26 }}
          />
          <div
            className="rounded"
            style={{ height: 4, background: preview.muted, width: 30 }}
          />
          <div
            className="rounded"
            style={{ height: 4, background: preview.muted, width: 20 }}
          />
        </div>
        {/* 疑似コンテンツ */}
        <div className="flex flex-1 flex-col gap-1.5 p-2">
          <div
            className="rounded"
            style={{ height: 5, background: preview.muted, width: "75%" }}
          />
          <div
            className="rounded"
            style={{ height: 5, background: preview.muted, width: "55%" }}
          />
          <div
            className="mt-1 rounded"
            style={{ height: 20, background: preview.border }}
          />
          <div
            className="rounded"
            style={{ height: 5, background: preview.muted, width: "65%" }}
          />
          <div
            className="rounded"
            style={{ height: 5, background: preview.muted, width: "45%" }}
          />
        </div>
      </div>
      {/* ラベル行 */}
      <div
        className="flex items-center justify-between px-3 py-2 text-xs font-medium"
        style={{
          background: preview.sidebar,
          borderTop: `1px solid ${preview.border}`,
          color: preview.text,
        }}
      >
        <div className="flex items-center gap-1.5">
          <theme.Icon size={12} />
          <span>{t(theme.labelKey)}</span>
        </div>
        {isSelected && <Check size={12} style={{ color: preview.accent }} />}
      </div>
    </button>
  );
};

// ─── SettingsDialog ──────────────────────────────────────────────────────────

export const SettingsDialog = ({
  open,
  onOpenChange,
}: SettingsDialogPropsType) => {
  const { t } = useTranslation();

  const theme = useSettingsStore((s) => s.theme);
  const language = useSettingsStore((s) => s.language);
  const encoding = useSettingsStore((s) => s.encoding);
  const logPath = useSettingsStore((s) => s.logPath);
  const setSettings = useSettingsStore((s) => s.setSettings);

  const [draft, setDraft] = useState<DraftSettingsType>({
    theme,
    language,
    encoding,
  });
  const [isSaving, setIsSaving] = useState(false);

  // ダイアログを開いた時点のテーマを記憶（キャンセル時に元に戻す）
  const originalThemeRef = useRef(theme);
  useEffect(() => {
    if (open) {
      originalThemeRef.current = theme;
    }
  }, [open, theme]);

  /** ダイアログを閉じる際に未保存のライブプレビューを元に戻す */
  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      document.documentElement.classList.toggle(
        "dark",
        originalThemeRef.current === "dark",
      );
    }
    onOpenChange(nextOpen);
  };

  /** テーマカード選択: draftを更新し即座に画面にプレビューを反映 */
  const handleThemeSelect = (themeId: string) => {
    setDraft((d) => ({ ...d, theme: themeId }));
    document.documentElement.classList.toggle("dark", themeId === "dark");
  };

  // ダイアログを開くたびに現在の設定で draft を初期化
  useEffect(() => {
    if (open) {
      setDraft({ theme, language, encoding });
    }
  }, [open, theme, language, encoding]);

  const isDirty =
    draft.theme !== theme ||
    draft.language !== language ||
    draft.encoding !== encoding;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await getEconomiconAPI().updateSettings({
        theme: draft.theme,
        language: draft.language,
        encoding: draft.encoding,
      });
      if (response.code === "OK" && response.result) {
        setSettings(response.result);
        onOpenChange(false);
      } else {
        await showMessageDialog(
          t("Error.Error"),
          getResponseErrorMessage(response, t("Error.UnexpectedError")),
        );
      }
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <BaseDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={t("SettingsDialog.Title")}
      maxWidth="2xl"
      footerVariant="confirm"
      submitLabel={
        isSaving ? t("SettingsDialog.Saving") : t("SettingsDialog.Save")
      }
      onSubmit={() => void handleSave()}
      isSubmitting={isSaving}
      isSubmitDisabled={!isDirty || isSaving}
      contentClassName="p-0"
    >
      {/* タブ + コンテンツ */}
      <Tabs.Root defaultValue="appearance" className="flex min-h-100">
        {/* 左サイドバー: タブリスト */}
        <Tabs.List
          className="flex w-44 shrink-0 flex-col gap-0.5 border-r border-gray-100 dark:border-gray-700 bg-gray-50/70 dark:bg-gray-900/60 p-3"
          aria-label={t("SettingsDialog.TabsLabel")}
        >
          {TABS.map((tab) => (
            <Tabs.Trigger
              key={tab.id}
              value={tab.id}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors",
                "text-gray-500 dark:text-gray-400 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 hover:text-gray-700 dark:hover:text-gray-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                "data-[state=active]:bg-white dark:data-[state=active]:bg-gray-800 data-[state=active]:text-gray-900 dark:data-[state=active]:text-gray-100 data-[state=active]:shadow-sm",
              )}
            >
              <tab.Icon size={15} aria-hidden="true" />
              <span>{t(tab.labelKey)}</span>
            </Tabs.Trigger>
          ))}
        </Tabs.List>

        {/* 右コンテンツエリア */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* ===== 外観タブ ===== */}
          <Tabs.Content
            value="appearance"
            className="flex-1 overflow-y-auto px-6 py-5"
          >
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {t("SettingsDialog.Theme.Label")}
            </h3>
            <p className="mb-4 mt-1 text-xs text-gray-400 dark:text-gray-500">
              {t("SettingsDialog.Theme.Description")}
            </p>
            <div className="grid grid-cols-3 gap-3">
              {THEMES.map((thm) => (
                <ThemeCard
                  key={thm.id}
                  theme={thm}
                  isSelected={draft.theme === thm.id}
                  onClick={() => handleThemeSelect(thm.id)}
                />
              ))}
            </div>
          </Tabs.Content>

          {/* ===== 一般タブ ===== */}
          <Tabs.Content
            value="general"
            className="flex-1 space-y-6 overflow-y-auto px-6 py-5"
          >
            {/* 言語 */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {t("SettingsDialog.Language.Label")}
              </h3>
              <div className="mt-2 flex gap-2">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.id}
                    type="button"
                    onClick={() =>
                      setDraft((d) => ({ ...d, language: lang.id }))
                    }
                    className={cn(
                      "rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
                      draft.language === lang.id
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                        : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700",
                    )}
                  >
                    {t(lang.labelKey)}
                  </button>
                ))}
              </div>
            </div>

            {/* エンコーディング */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {t("SettingsDialog.Encoding.Label")}
              </h3>
              <Select.Root
                value={draft.encoding}
                onValueChange={(v) => setDraft((d) => ({ ...d, encoding: v }))}
              >
                <Select.Trigger
                  className={cn(
                    "mt-2 flex h-9 w-48 items-center justify-between rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 text-sm text-gray-700 dark:text-gray-200",
                    "hover:border-gray-300 dark:hover:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500",
                  )}
                >
                  <Select.Value />
                  <Select.Icon>
                    <ChevronDown
                      size={14}
                      className="text-gray-400 dark:text-gray-500"
                    />
                  </Select.Icon>
                </Select.Trigger>
                <Select.Portal>
                  <Select.Content
                    className="z-100 overflow-hidden rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg"
                    position="popper"
                    sideOffset={4}
                  >
                    <Select.Viewport className="p-1">
                      {ENCODINGS.map((enc) => (
                        <Select.Item
                          key={enc}
                          value={enc}
                          className={cn(
                            "flex cursor-pointer items-center rounded px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200",
                            "hover:bg-gray-100 dark:hover:bg-gray-700 focus:bg-gray-100 dark:focus:bg-gray-700 focus:outline-none",
                            "data-[state=checked]:font-medium data-[state=checked]:text-blue-600 dark:data-[state=checked]:text-blue-400",
                          )}
                        >
                          <Select.ItemText>{enc}</Select.ItemText>
                          <Select.ItemIndicator className="ml-auto pl-2">
                            <Check size={12} className="text-blue-500" />
                          </Select.ItemIndicator>
                        </Select.Item>
                      ))}
                    </Select.Viewport>
                  </Select.Content>
                </Select.Portal>
              </Select.Root>
            </div>
          </Tabs.Content>

          {/* ===== データタブ（将来実装） ===== */}
          <Tabs.Content
            value="data"
            className="flex-1 overflow-y-auto px-6 py-5"
          >
            <p className="text-sm text-gray-400 dark:text-gray-500">
              {t("SettingsDialog.Placeholder")}
            </p>
          </Tabs.Content>

          {/* ===== ログタブ ===== */}
          <Tabs.Content
            value="log"
            className="flex-1 overflow-y-auto px-6 py-5"
          >
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {t("SettingsDialog.LogPath.Label")}
            </h3>
            <p className="mt-2 break-all rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2 font-mono text-xs text-gray-500 dark:text-gray-400">
              {logPath || t("SettingsDialog.LogPath.NotSet")}
            </p>
          </Tabs.Content>
        </div>
      </Tabs.Root>
    </BaseDialog>
  );
};
