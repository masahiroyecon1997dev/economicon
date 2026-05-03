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
});