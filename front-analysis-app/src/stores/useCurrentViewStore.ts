import { create } from "zustand";

export type CurrentViewValue =
  | "ImportDataFile"
  | "LinearRegressionForm"
  | "CreateSimulationDataTable"
  | "CalculationView"
  | "SaveData"
  | "DataPreview";

export type CurrentViewActions = {
  setCurrentView: (view: CurrentViewValue) => void;
};

type CurrentViewStore = {
  currentView: CurrentViewValue;
} & CurrentViewActions;

export const useCurrentViewStore = create<CurrentViewStore>((set) => ({
  currentView: "ImportDataFile",
  setCurrentView: (view) => set({ currentView: view }),
}));
