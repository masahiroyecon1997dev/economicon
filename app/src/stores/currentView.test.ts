import { beforeEach, describe, expect, it } from "vitest";
import type { CurrentPageValue } from "./currentView";
import { useCurrentPageStore } from "./currentView";

beforeEach(() => {
  useCurrentPageStore.setState({ currentView: "ImportDataFile" });
});

describe("useCurrentPageStore", () => {
  describe("initial state", () => {
    it("test_initialState_isImportDataFile", () => {
      expect(useCurrentPageStore.getState().currentView).toBe("ImportDataFile");
    });
  });

  describe("setCurrentView", () => {
    const views: CurrentPageValue[] = [
      "ImportDataFile",
      "JoinTable",
      "UnionTable",
      "DescriptiveStatistics",
      "CorrelationMatrix",
      "ConfidenceIntervalView",
      "LinearRegressionForm",
      "CreateSimulationDataTable",
      "CalculationView",
      "SaveData",
      "DataPreview",
    ];

    it.each(views)("test_setCurrentView_%s_updatesCurrentView", (view) => {
      const { setCurrentView } = useCurrentPageStore.getState();
      setCurrentView(view);

      expect(useCurrentPageStore.getState().currentView).toBe(view);
    });

    it("test_setCurrentView_canSwitchMultipleTimes", () => {
      const { setCurrentView } = useCurrentPageStore.getState();
      setCurrentView("SaveData");
      setCurrentView("DescriptiveStatistics");

      expect(useCurrentPageStore.getState().currentView).toBe(
        "DescriptiveStatistics",
      );
    });
  });
});
