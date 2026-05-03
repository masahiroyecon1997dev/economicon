import type { WorkFeatureKey } from "@/stores/workspaceTabs";

export type WorkTabEntry = {
  featureKey: WorkFeatureKey;
  titleKey: string;
};

export const WORK_TAB_ENTRIES: WorkTabEntry[] = [
  {
    featureKey: "JoinTable",
    titleKey: "HeaderMenu.JoinTable",
  },
  {
    featureKey: "UnionTable",
    titleKey: "HeaderMenu.UnionTable",
  },
  {
    featureKey: "CreateSimulationDataTable",
    titleKey: "HeaderMenu.DataGeneration",
  },
  {
    featureKey: "CalculationView",
    titleKey: "HeaderMenu.Calculate",
  },
  {
    featureKey: "ConfidenceIntervalView",
    titleKey: "HeaderMenu.ConfidenceInterval",
  },
  {
    featureKey: "LinearRegressionForm",
    titleKey: "HeaderMenu.OrdinaryLeastSquares",
  },
  {
    featureKey: "CorrelationMatrix",
    titleKey: "HeaderMenu.CorrelationMatrix",
  },
];

export const isWorkFeatureKey = (value: string): value is WorkFeatureKey =>
  WORK_TAB_ENTRIES.some((entry) => entry.featureKey === value);