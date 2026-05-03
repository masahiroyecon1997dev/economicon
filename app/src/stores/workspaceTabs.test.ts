import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { beforeEach, describe, expect, it } from "vitest";

describe("workspaceTabs store", () => {
  beforeEach(() => {
    useWorkspaceTabsStore.setState({
      tabs: [],
      activeTabId: null,
    });
  });

  it("openWorkTab は同じ featureKey の既存 work tab を再利用する", () => {
    const firstId = useWorkspaceTabsStore
      .getState()
      .openWorkTab("JoinTable", "ジョイン");

    useWorkspaceTabsStore.getState().setWorkTabDirty(firstId, true);

    const secondId = useWorkspaceTabsStore
      .getState()
      .openWorkTab("JoinTable", "ジョイン");

    const state = useWorkspaceTabsStore.getState();
    expect(firstId).toBe("work:JoinTable");
    expect(secondId).toBe("work:JoinTable");
    expect(state.tabs).toHaveLength(1);
    expect(state.tabs[0]).toMatchObject({
      id: "work:JoinTable",
      kind: "work",
      featureKey: "JoinTable",
      title: "ジョイン",
      dirty: true,
    });
    expect(typeof state.tabs[0]?.createdAt).toBe("number");
    expect(state.activeTabId).toBe("work:JoinTable");
  });

  it("featureKey が違えば別の work tab を持てる", () => {
    useWorkspaceTabsStore.getState().openWorkTab("JoinTable", "ジョイン");
    useWorkspaceTabsStore
      .getState()
      .openWorkTab("CalculationView", "計算");

    const state = useWorkspaceTabsStore.getState();
    expect(state.tabs).toHaveLength(2);
    expect(state.tabs.map((tab) => tab.id)).toEqual([
      "work:JoinTable",
      "work:CalculationView",
    ]);
    expect(state.activeTabId).toBe("work:CalculationView");
  });

  it("draft 更新は committedValues との差分で dirty を判定する", () => {
    const tabId = useWorkspaceTabsStore
      .getState()
      .openWorkTab("CorrelationMatrix", "相関行列");

    useWorkspaceTabsStore.getState().ensureWorkTabState(tabId, {
      tableName: "sales",
      columnNames: ["price", "quantity"],
    });
    useWorkspaceTabsStore.getState().updateWorkTabDraft(tabId, {
      tableName: "sales",
      columnNames: ["price"],
    });

    let tab = useWorkspaceTabsStore
      .getState()
      .tabs.find((item) => item.id === tabId);
    expect(tab).toMatchObject({
      kind: "work",
      dirty: true,
      draftValues: {
        tableName: "sales",
        columnNames: ["price"],
      },
      committedValues: {
        tableName: "sales",
        columnNames: ["price", "quantity"],
      },
    });

    useWorkspaceTabsStore.getState().updateWorkTabDraft(tabId, {
      tableName: "sales",
      columnNames: ["price", "quantity"],
    });

    tab = useWorkspaceTabsStore.getState().tabs.find((item) => item.id === tabId);
    expect(tab).toMatchObject({
      kind: "work",
      dirty: false,
    });
  });

  it("commitWorkTab は draft と committed を同期して dirty を false に戻す", () => {
    const tabId = useWorkspaceTabsStore
      .getState()
      .openWorkTab("CorrelationMatrix", "相関行列");

    useWorkspaceTabsStore.getState().ensureWorkTabState(tabId, {
      tableName: "sales",
      newTableName: "corr_a",
    });
    useWorkspaceTabsStore.getState().updateWorkTabDraft(tabId, {
      tableName: "sales",
      newTableName: "corr_b",
    });
    useWorkspaceTabsStore.getState().commitWorkTab(tabId, {
      tableName: "sales",
      newTableName: "corr_b",
    });

    const tab = useWorkspaceTabsStore
      .getState()
      .tabs.find((item) => item.id === tabId);

    expect(tab).toMatchObject({
      kind: "work",
      dirty: false,
      draftValues: {
        tableName: "sales",
        newTableName: "corr_b",
      },
      committedValues: {
        tableName: "sales",
        newTableName: "corr_b",
      },
    });
  });
});