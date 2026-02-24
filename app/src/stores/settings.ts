import type { GetSettingsResult } from "@/api/model";
import { create } from "zustand";

/** Tauri get_os_info コマンドから取得するOS情報 */
export type OsInfo = {
  osName: string;
  pathSeparator: string;
};

export type SettingsActions = {
  setSettings: (newSettings: GetSettingsResult) => void;
  setOsInfo: (osInfo: OsInfo) => void;
};

type SettingsStore = GetSettingsResult & OsInfo & SettingsActions;

export const useSettingsStore = create<SettingsStore>((set) => ({
  language: "",
  lastOpenedPath: "",
  theme: "",
  encoding: "",
  logPath: "",
  osName: "",
  pathSeparator: "/",
  setSettings: (newSettings) => {
    set(newSettings);
  },
  setOsInfo: (osInfo) => {
    set(osInfo);
  },
}));
