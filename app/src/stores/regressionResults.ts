import { create } from "zustand";
import type { LinearRegressionResultType } from "../types/commonTypes";

export type RegressionResultsActions = {
  addResult: (result: LinearRegressionResultType) => void;
  removeResult: (resultId: string) => void;
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
    removeResult: (resultId) =>
      set((state) => ({
        results: state.results.filter((r) => r.resultId !== resultId),
      })),
  }),
);
