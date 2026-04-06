import { create } from "zustand";

// GET /api/analysis/results/{id} の resultData に格納される信頼区間の計算結果
// TODO: 信頼区間のAPIが変更されIDをバックエンドで生成するようになったため、idはバックエンドから受け取るようにすること
export type ConfidenceIntervalResultData = {
  tableName: string;
  columnName: string;
  statistic: { type: string; value: number | null };
  confidenceInterval: { lower: number; upper: number };
  confidenceLevel: number;
};

export type ConfidenceIntervalResultEntry = ConfidenceIntervalResultData & {
  id: string;
};

type ConfidenceIntervalResultsActions = {
  addResult: (result: ConfidenceIntervalResultData) => void;
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
        results: [...state.results, { ...result, id: crypto.randomUUID() }],
      })),
    removeResult: (id) =>
      set((state) => ({
        results: state.results.filter((r) => r.id !== id),
      })),
  }));
