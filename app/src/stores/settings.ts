import type { GetSettingsResult } from "@/api/model";
import { create } from "zustand";

export type SettingsActions = {
  setSettings: (newSettings: GetSettingsResult) => void;
};
type SettingsStore = GetSettingsResult & SettingsActions;

export const useSettingsStore = create<SettingsStore>((set) => ({
  language: "",
  lastOpenedPath: "",
  theme: "",
  encoding: "",
  logPath: "",
  setSettings: (newSettings) => {
    set(newSettings);
  },
}));
