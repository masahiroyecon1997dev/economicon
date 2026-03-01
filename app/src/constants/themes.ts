/**
 * アプリケーションテーマ定義
 *
 * 新しいテーマを追加する場合は THEMES 配列にオブジェクトを追加するだけでよい。
 * バックエンドの `UpdateSettingsRequest.theme` バリデーションも合わせて更新すること。
 */
import type { LucideIcon } from "lucide-react";
import { Moon, Sun } from "lucide-react";

export type ThemePreviewType = {
  readonly bg: string;
  readonly sidebar: string;
  readonly border: string;
  readonly text: string;
  readonly accent: string;
  readonly muted: string;
};

export type ThemeDefinitionType = {
  readonly id: string;
  /** i18n キー（例: "SettingsDialog.Theme.Light"） */
  readonly labelKey: string;
  readonly Icon: LucideIcon;
  /** SettingsDialog のミニプレビュー用カラーパレット */
  readonly preview: ThemePreviewType;
};

export const THEMES: readonly ThemeDefinitionType[] = [
  {
    id: "light",
    labelKey: "SettingsDialog.Theme.Light",
    Icon: Sun,
    preview: {
      bg: "#ffffff",
      sidebar: "#f9fafb",
      border: "#e5e7eb",
      text: "#374151",
      accent: "#3b82f6",
      muted: "#d1d5db",
    },
  },
  {
    id: "dark",
    labelKey: "SettingsDialog.Theme.Dark",
    Icon: Moon,
    preview: {
      bg: "#1e2532",
      sidebar: "#161c27",
      border: "#2d3748",
      text: "#e2e8f0",
      accent: "#60a5fa",
      muted: "#4a5568",
    },
  },
];

export type ThemeId = (typeof THEMES)[number]["id"];
