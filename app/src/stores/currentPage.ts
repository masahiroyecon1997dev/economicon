import { create } from "zustand";

export type ShellPageValue = "ImportDataFile" | "SaveData";
export type CurrentPageValue = ShellPageValue | "Workspace";

type CurrentPageStore = {
  currentView: CurrentPageValue;
  navigateToShell: (shell: ShellPageValue) => void;
  navigateToWorkspace: () => void;
};

export const useCurrentPageStore = create<CurrentPageStore>((set) => ({
  currentView: "ImportDataFile",
  navigateToShell: (shell) => set({ currentView: shell }),
  navigateToWorkspace: () => set({ currentView: "Workspace" }),
}));
