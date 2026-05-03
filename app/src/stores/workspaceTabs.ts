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

export type WorkFeatureKey =
  | "JoinTable"
  | "UnionTable"
  | "CreateSimulationDataTable"
  | "CalculationView"
  | "ConfidenceIntervalView"
  | "LinearRegressionForm"
  | "CorrelationMatrix";

export type WorkspaceWorkTab = {
  id: `work:${WorkFeatureKey}`;
  kind: "work";
  title: string;
  featureKey: WorkFeatureKey;
  dirty: boolean;
  createdAt: number;
  draftValues?: unknown;
  committedValues?: unknown;
};

export type WorkspaceTab =
  | WorkspaceDataTab
  | WorkspaceResultTab
  | WorkspaceWorkTab;

type WorkspaceTabsState = {
  tabs: WorkspaceTab[];
  activeTabId: string | null;
};

type WorkspaceTabsActions = {
  openDataTab: (tableName: string) => void;
  openResultTab: (detail: AnalysisResultDetail) => void;
  openWorkTab: (featureKey: WorkFeatureKey, title: string) => string;
  setWorkTabDirty: (tabId: string, dirty: boolean) => void;
  ensureWorkTabState: (tabId: string, initialValues: unknown) => void;
  updateWorkTabDraft: (tabId: string, draftValues: unknown) => void;
  commitWorkTab: (tabId: string, values: unknown) => void;
  activateTab: (tabId: string) => void;
  closeTab: (tabId: string) => void;
  syncDataTabs: (
    tableNames: string[],
    activeTableName: string | null,
    preserveActiveNonData: boolean,
  ) => void;
  pruneMissingDataTabs: (tableNames: string[]) => void;
  removeResultTab: (resultId: string) => void;
  updateResultTabTitle: (resultId: string, title: string) => void;
  updateResultTabDetail: (
    resultId: string,
    detail: AnalysisResultDetail,
  ) => void;
};

type WorkspaceTabsStore = WorkspaceTabsState & WorkspaceTabsActions;

const toWorkTabId = (featureKey: WorkFeatureKey): `work:${WorkFeatureKey}` =>
  `work:${featureKey}`;

const cloneWorkTabValues = <T,>(values: T): T => {
  if (values === undefined) {
    return values;
  }
  return JSON.parse(JSON.stringify(values)) as T;
};

const areWorkTabValuesEqual = (left: unknown, right: unknown) =>
  JSON.stringify(left) === JSON.stringify(right);

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

  syncDataTabs: (tableNames, activeTableName, preserveActiveNonData) =>
    set((state) => {
      const nextTabs = state.tabs.filter(
        (tab) => tab.kind !== "data" || tableNames.includes(tab.tableName),
      );

      for (const tableName of tableNames) {
        const tabId: `data:${string}` = `data:${tableName}`;
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
        preserveActiveNonData && activeTabExists
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

  openWorkTab: (featureKey, title) => {
    const tabId = toWorkTabId(featureKey);
    set((state) => {
      const existingIndex = state.tabs.findIndex((tab) => tab.id === tabId);
      if (existingIndex !== -1) {
        const nextTabs = [...state.tabs];
        const existingTab = nextTabs[existingIndex];
        if (existingTab?.kind === "work") {
          nextTabs[existingIndex] = { ...existingTab, title };
        }
        return {
          tabs: nextTabs,
          activeTabId: tabId,
        };
      }

      return {
        tabs: [
          ...state.tabs,
          {
            id: tabId,
            kind: "work" as const,
            title,
            featureKey,
            dirty: false,
            createdAt: Date.now(),
          },
        ],
        activeTabId: tabId,
      };
    });
    return tabId;
  },

  setWorkTabDirty: (tabId, dirty) =>
    set((state) => {
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "work") return {};
      nextTabs[index] = { ...tab, dirty };
      return { tabs: nextTabs };
    }),

  ensureWorkTabState: (tabId, initialValues) =>
    set((state) => {
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "work") return {};
      if (tab.draftValues !== undefined || tab.committedValues !== undefined) {
        return {};
      }
      const snapshot = cloneWorkTabValues(initialValues);
      nextTabs[index] = {
        ...tab,
        draftValues: snapshot,
        committedValues: snapshot,
        dirty: false,
      };
      return { tabs: nextTabs };
    }),

  updateWorkTabDraft: (tabId, draftValues) =>
    set((state) => {
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "work") return {};

      const nextDraftValues = cloneWorkTabValues(draftValues);
      const committedValues =
        tab.committedValues === undefined
          ? nextDraftValues
          : tab.committedValues;

      nextTabs[index] = {
        ...tab,
        draftValues: nextDraftValues,
        committedValues,
        dirty: !areWorkTabValuesEqual(nextDraftValues, committedValues),
      };
      return { tabs: nextTabs };
    }),

  commitWorkTab: (tabId, values) =>
    set((state) => {
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "work") return {};

      const snapshot = cloneWorkTabValues(values);
      nextTabs[index] = {
        ...tab,
        draftValues: snapshot,
        committedValues: snapshot,
        dirty: false,
      };
      return { tabs: nextTabs };
    }),

  updateResultTabTitle: (resultId, title) =>
    set((state) => {
      const tabId = `result:${resultId}`;
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "result") return {};
      nextTabs[index] = { ...tab, title };
      return { tabs: nextTabs };
    }),

  updateResultTabDetail: (resultId, detail) =>
    set((state) => {
      const tabId = `result:${resultId}`;
      const index = state.tabs.findIndex((tab) => tab.id === tabId);
      if (index === -1) return {};
      const nextTabs = [...state.tabs];
      const tab = nextTabs[index];
      if (tab?.kind !== "result") return {};
      nextTabs[index] = { ...tab, title: detail.name, detail };
      return { tabs: nextTabs };
    }),
}));
