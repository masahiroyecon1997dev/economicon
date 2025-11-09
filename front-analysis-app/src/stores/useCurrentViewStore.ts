import { create } from "zustand";

export type CurrentViewType = { currentView: string };

export type CurrentViewActions = {
  setCurrentView: (view: CurrentViewType) => void;
}

type CurrentViewStore = CurrentViewType & CurrentViewActions;

export const useCurrentViewStore = create<CurrentViewStore>((set) => ({
  currentView: "selectFile",
  setCurrentView: (view) => set(() => (view)),
}));
