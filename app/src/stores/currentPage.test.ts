import type { CurrentPageValue, ShellPageValue } from "@/stores/currentPage";
import { useCurrentPageStore } from "@/stores/currentPage";
import { beforeEach, describe, expect, it } from "vitest";

beforeEach(() => {
  useCurrentPageStore.setState({ currentView: "ImportDataFile" });
});

describe("useCurrentPageStore", () => {
  describe("initial state", () => {
    it("test_initialState_isImportDataFile", () => {
      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });
  });

  describe("navigateToShell", () => {
    const shells: ShellPageValue[] = ["ImportDataFile", "SaveData"];

    it.each(shells)("test_navigateToShell_%s_updatesCurrentView", (shell) => {
      const { navigateToShell } = useCurrentPageStore.getState();
      navigateToShell(shell);

      expect(useCurrentPageStore.getState().currentView).toBe(shell);
    });
  });

  describe("navigateToWorkspace", () => {
    it("test_navigateToWorkspace_setsWorkspace", () => {
      const { navigateToWorkspace } = useCurrentPageStore.getState();
      navigateToWorkspace();

      expect(useCurrentPageStore.getState().currentView).toBe("Workspace");
    });
  });

  describe("CurrentPageValue type", () => {
    const views: CurrentPageValue[] = [
      "ImportDataFile",
      "SaveData",
      "Workspace",
    ];

    it.each(views)("test_currentPageValue_%s_isValid", (view) => {
      useCurrentPageStore.setState({ currentView: view });
      expect(useCurrentPageStore.getState().currentView).toBe(view);
    });
  });
});
