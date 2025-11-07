import { create } from "zustand";
import type { SettingsType } from "../types/commonTypes";

export type SettingsStateType = { settings: SettingsType }

export type SettingsActions = {
  setSettings: (settings: SettingsStateType) => void;
}
type SettingsStore = SettingsStateType & SettingsActions;

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: {
    defaultFolderPath: "",
    displayRows: 0,
    appLanguage: "",
    encoding: "",
    pathSeparator: "",
  },
  setSettings: (settings) => set(() => (settings))
}));
