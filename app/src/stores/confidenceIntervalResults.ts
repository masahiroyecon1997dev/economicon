import { create } from "zustand";
import type { ConfidenceIntervalResult } from "../api/model";

export type ConfidenceIntervalResultEntry = ConfidenceIntervalResult & {
  id: string;
};

type ConfidenceIntervalResultsActions = {
  addResult: (result: ConfidenceIntervalResult) => void;
  removeResult: (id: string) => void;
};

type ConfidenceIntervalResultsStore = {
  results: ConfidenceIntervalResultEntry[];
} & ConfidenceIntervalResultsActions;

export const useConfidenceIntervalResultsStore =
  create<ConfidenceIntervalResultsStore>((set) => ({
    results: [],
    addResult: (result) =>
      set((state) => ({
        results: [
          ...state.results,
          { ...result, id: crypto.randomUUID() },
        ],
      })),
    removeResult: (id) =>
      set((state) => ({
        results: state.results.filter((r) => r.id !== id),
      })),
  }));
