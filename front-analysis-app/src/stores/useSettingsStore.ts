import { create } from "zustand";
import type { SettingsType } from "../types/commonTypes";

export type SettingsActions = {
  setSettings: (newSettings: SettingsType) => void;
};
type SettingsStore = SettingsType & SettingsActions;

export const useSettingsStore = create<SettingsStore>((set) => ({
  osName: "",
  defaultFolderPath: "",
  displayRows: 0,
  appLanguage: "",
  encoding: "",
  pathSeparator: "",
  setSettings: (newSettings) => {
    set(newSettings);
  },
}));
