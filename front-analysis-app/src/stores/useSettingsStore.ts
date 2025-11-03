import { create } from "zustand";
import type { SettingsType } from "../types/stateTypes";

export type SettingsActions = {
  setSettings: (settings: SettingsType) => void;
}

type SettingsStore = SettingsType & SettingsActions;

const useSettingsStore = create<SettingsStore>((set) => ({
  settings: {
    defaultFolderPath: "",
    displayRows: 0,
    appLanguage: ""
  },
  setSettings: (settings) => set(() => ({ ...settings }))
}));

export default useSettingsStore;
