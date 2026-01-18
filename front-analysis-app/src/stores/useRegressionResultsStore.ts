import { create } from "zustand";
import type { LinearRegressionResultType } from "../types/commonTypes";

export type RegressionResultsActions = {
  addResult: (result: LinearRegressionResultType) => void;
  clearResults: () => void;
  removeResult: (index: number) => void;
};

type RegressionResultsStore = {
  results: LinearRegressionResultType[];
} & RegressionResultsActions;

export const useRegressionResultsStore = create<RegressionResultsStore>(
  (set) => ({
    results: [],
    addResult: (result) =>
      set((state) => ({
        results: [...state.results, result],
      })),
    clearResults: () => set({ results: [] }),
    removeResult: (index) =>
      set((state) => ({
        results: state.results.filter((_, i) => i !== index),
      })),
  }),
);
