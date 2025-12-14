import { create } from "zustand";

export type CurrentViewValue =
  | "SelectFile"
  | "LinearRegressionForm"
  | "CreateSimulationDataTable"
  | "SaveData"
  | "DataPreview";

export type CurrentViewActions = {
  setCurrentView: (view: CurrentViewValue) => void;
};

type CurrentViewStore = {
  currentView: CurrentViewValue;
} & CurrentViewActions;

export const useCurrentViewStore = create<CurrentViewStore>((set) => ({
  currentView: "SelectFile",
  setCurrentView: (view) => set({ currentView: view }),
}));
