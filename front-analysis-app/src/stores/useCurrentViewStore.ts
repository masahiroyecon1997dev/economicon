import { create } from "zustand";

export type CurrentViewValue =
  "selectFile" |
  "LinearRegressionForm" |
  "dataPreview";

export type CurrentViewActions = {
  setCurrentView: (view: CurrentViewValue) => void;
}

type CurrentViewStore = {
    currentView: CurrentViewValue;
} & CurrentViewActions;

export const useCurrentViewStore = create<CurrentViewStore>((set) => ({
  currentView: "selectFile",
  setCurrentView: (view) => set({ currentView: view }),
}));
