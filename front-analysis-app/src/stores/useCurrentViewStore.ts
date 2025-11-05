import { create } from "zustand";
import type { CurrentViewType } from "../types/stateTypes";


export type CurrentViewActions = {
  setCurrentView: (view: CurrentViewType) => void;
}

type CurrentViewStore = CurrentViewType & CurrentViewActions;

const useCurrentViewStore = create<CurrentViewStore>((set) => ({
  currentView: "selectFile",
  setCurrentView: (view) => set(() => (view)),
}));

export default useCurrentViewStore;
