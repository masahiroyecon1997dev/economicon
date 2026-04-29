import { create } from "zustand";

// GET /api/analysis/results/{id} の resultData に格納される信頼区間の計算結果
export type ConfidenceIntervalResultData = {
  resultId: string;
  tableName: string;
  columnName: string;
  statistic: { type: string; value: number | null };
  confidenceInterval: { lower: number; upper: number };
  confidenceLevel: number;
};

export type ConfidenceIntervalResultEntry = ConfidenceIntervalResultData;

type ConfidenceIntervalResultsActions = {
  addResult: (result: ConfidenceIntervalResultData) => void;
  removeResult: (resultId: string) => void;
};

type ConfidenceIntervalResultsStore = {
  results: ConfidenceIntervalResultEntry[];
} & ConfidenceIntervalResultsActions;

export const useConfidenceIntervalResultsStore =
  create<ConfidenceIntervalResultsStore>((set) => ({
    results: [],
    addResult: (result) =>
      set((state) => ({
        results: [...state.results, result],
      })),
    removeResult: (resultId) =>
      set((state) => ({
        results: state.results.filter((r) => r.resultId !== resultId),
      })),
  }));
