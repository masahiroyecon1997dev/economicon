import type { AnalysisResultDetail } from "@/api/model";
import { create } from "zustand";

export type WorkspaceDataTab = {
  id: `data:${string}`;
  kind: "data";
  title: string;
  tableName: string;
};

export type WorkspaceResultTab = {
  id: `result:${string}`;
  kind: "result";
  title: string;
  resultId: string;
  resultType: string;
  detail: AnalysisResultDetail;
};

export type WorkspaceTab = WorkspaceDataTab | WorkspaceResultTab;

type WorkspaceTabsState = {
  tabs: WorkspaceTab[];
  activeTabId: string | null;
};

type WorkspaceTabsActions = {
  openDataTab: (tableName: string) => void;
  openResultTab: (detail: AnalysisResultDetail) => void;
  activateTab: (tabId: string) => void;
  closeTab: (tabId: string) => void;
  syncDataTabs: (
    tableNames: string[],
    activeTableName: string | null,
    preserveActiveResult: boolean,
  ) => void;
  pruneMissingDataTabs: (tableNames: string[]) => void;
  removeResultTab: (resultId: string) => void;
};

type WorkspaceTabsStore = WorkspaceTabsState & WorkspaceTabsActions;

const nextActiveTabId = (
  tabs: WorkspaceTab[],
  removedTabId: string,
): string | null => {
  const index = tabs.findIndex((tab) => tab.id === removedTabId);
  const remainingTabs = tabs.filter((tab) => tab.id !== removedTabId);
  if (remainingTabs.length === 0) return null;
  const nextIndex = Math.min(index, remainingTabs.length - 1);
  return remainingTabs[nextIndex]?.id ?? null;
};

export const useWorkspaceTabsStore = create<WorkspaceTabsStore>((set) => ({
  tabs: [],
  activeTabId: null,

  openDataTab: (tableName) =>
    set((state) => {
      const tabId = `data:${tableName}` as const;
      const existingTab = state.tabs.find((tab) => tab.id === tabId);
      if (existingTab) {
        return { activeTabId: tabId };
      }

      return {
        tabs: [
          ...state.tabs,
          {
            id: tabId,
            kind: "data",
            title: tableName,
            tableName,
          },
        ],
        activeTabId: tabId,
      };
    }),

  openResultTab: (detail) =>
    set((state) => {
      const tabId = `result:${detail.id}` as const;
      const nextTab: WorkspaceResultTab = {
        id: tabId,
        kind: "result",
        title: detail.name,
        resultId: detail.id,
        resultType: detail.resultType,
        detail,
      };

      const existingIndex = state.tabs.findIndex((tab) => tab.id === tabId);
      if (existingIndex !== -1) {
        const nextTabs = [...state.tabs];
        nextTabs[existingIndex] = nextTab;
        return { tabs: nextTabs, activeTabId: tabId };
      }

      return {
        tabs: [...state.tabs, nextTab],
        activeTabId: tabId,
      };
    }),

  activateTab: (tabId) => set({ activeTabId: tabId }),

  closeTab: (tabId) =>
    set((state) => ({
      tabs: state.tabs.filter((tab) => tab.id !== tabId),
      activeTabId:
        state.activeTabId === tabId
          ? nextActiveTabId(state.tabs, tabId)
          : state.activeTabId,
    })),

  syncDataTabs: (tableNames, activeTableName, preserveActiveResult) =>
    set((state) => {
      const nextTabs = state.tabs.filter(
        (tab) => tab.kind !== "data" || tableNames.includes(tab.tableName),
      );

      for (const tableName of tableNames) {
        const tabId = `data:${tableName}`;
        if (!nextTabs.some((tab) => tab.id === tabId)) {
          nextTabs.push({
            id: tabId,
            kind: "data",
            title: tableName,
            tableName,
          });
        }
      }

      const activeTabExists = nextTabs.some(
        (tab) => tab.id === state.activeTabId,
      );
      const nextActiveTabId =
        preserveActiveResult && activeTabExists
          ? state.activeTabId
          : activeTableName
            ? (`data:${activeTableName}` as const)
            : (nextTabs.at(-1)?.id ?? null);

      return {
        tabs: nextTabs,
        activeTabId: nextActiveTabId,
      };
    }),

  pruneMissingDataTabs: (tableNames) =>
    set((state) => {
      const nextTabs = state.tabs.filter(
        (tab) => tab.kind !== "data" || tableNames.includes(tab.tableName),
      );
      const activeTabExists = nextTabs.some(
        (tab) => tab.id === state.activeTabId,
      );
      return {
        tabs: nextTabs,
        activeTabId: activeTabExists
          ? state.activeTabId
          : (nextTabs.at(-1)?.id ?? null),
      };
    }),

  removeResultTab: (resultId) =>
    set((state) => {
      const tabId = `result:${resultId}`;
      return {
        tabs: state.tabs.filter((tab) => tab.id !== tabId),
        activeTabId:
          state.activeTabId === tabId
            ? nextActiveTabId(state.tabs, tabId)
            : state.activeTabId,
      };
    }),
}));
