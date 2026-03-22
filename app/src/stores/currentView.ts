import { create } from "zustand";

export type CurrentPageValue =
  | "ImportDataFile"
  | "JoinTable"
  | "UnionTable"
  | "DescriptiveStatistics"
  | "LinearRegressionForm"
  | "CreateSimulationDataTable"
  | "CalculationView"
  | "SaveData"
  | "DataPreview";

export type CurrentPageActions = {
  setCurrentView: (view: CurrentPageValue) => void;
};

type CurrentPageStore = {
  currentView: CurrentPageValue;
} & CurrentPageActions;

export const useCurrentPageStore = create<CurrentPageStore>((set) => ({
  currentView: "ImportDataFile",
  setCurrentView: (view) => set({ currentView: view }),
}));
