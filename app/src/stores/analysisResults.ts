import type { AnalysisResultDetail, AnalysisResultSummary } from "@/api/model";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { create } from "zustand";

export type AnalysisResultsPane = "data" | "results";

type AnalysisResultsState = {
  pane: AnalysisResultsPane;
  summaries: AnalysisResultSummary[];
  activeResultId: string | null;
  activeResultDetail: AnalysisResultDetail | null;
  isListLoading: boolean;
  isDetailLoading: boolean;
};

type AnalysisResultsActions = {
  setPane: (pane: AnalysisResultsPane) => void;
  setActiveResult: (
    resultId: string | null,
    detail?: AnalysisResultDetail | null,
  ) => void;
  fetchSummaries: () => Promise<void>;
  openResult: (resultId: string) => Promise<AnalysisResultDetail>;
  removeSummary: (resultId: string) => void;
  upsertSummary: (summary: AnalysisResultSummary) => void;
  clearActiveResult: () => void;
};

type AnalysisResultsStore = AnalysisResultsState & AnalysisResultsActions;

export const useAnalysisResultsStore = create<AnalysisResultsStore>((set) => ({
  pane: "data",
  summaries: [],
  activeResultId: null,
  activeResultDetail: null,
  isListLoading: false,
  isDetailLoading: false,

  setPane: (pane) => set({ pane }),

  setActiveResult: (resultId, detail = null) =>
    set({
      activeResultId: resultId,
      activeResultDetail: detail,
    }),

  fetchSummaries: async () => {
    set({ isListLoading: true });
    try {
      const response = await getEconomiconAppAPI().getAllAnalysisResults();
      set({ summaries: response.result.results, isListLoading: false });
    } catch {
      set({ isListLoading: false });
      throw new Error("FAILED_TO_FETCH_ANALYSIS_RESULTS");
    }
  },

  openResult: async (resultId) => {
    set({ isDetailLoading: true });
    try {
      const response = await getEconomiconAppAPI().getAnalysisResult(resultId);
      set({
        activeResultId: resultId,
        activeResultDetail: response.result,
        isDetailLoading: false,
      });
      return response.result;
    } catch {
      set({ isDetailLoading: false });
      throw new Error("FAILED_TO_FETCH_ANALYSIS_RESULT");
    }
  },

  removeSummary: (resultId) =>
    set((state) => ({
      summaries: state.summaries.filter((result) => result.id !== resultId),
      activeResultId:
        state.activeResultId === resultId ? null : state.activeResultId,
      activeResultDetail:
        state.activeResultId === resultId ? null : state.activeResultDetail,
    })),

  upsertSummary: (summary) =>
    set((state) => {
      const existingIndex = state.summaries.findIndex(
        (result) => result.id === summary.id,
      );
      if (existingIndex === -1) {
        return { summaries: [summary, ...state.summaries] };
      }

      const nextSummaries = [...state.summaries];
      nextSummaries[existingIndex] = summary;
      return { summaries: nextSummaries };
    }),

  clearActiveResult: () =>
    set({
      activeResultId: null,
      activeResultDetail: null,
      isDetailLoading: false,
    }),
}));
