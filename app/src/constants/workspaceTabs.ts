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
    featureKey: "DescriptiveStatistics",
    titleKey: "HeaderMenu.BasicStatistics",
  },
  {
    featureKey: "ConfidenceIntervalView",
    titleKey: "HeaderMenu.ConfidenceInterval",
  },
  {
    featureKey: "StatisticalTestView",
    titleKey: "HeaderMenu.HypothesisTest",
  },
  {
    featureKey: "LinearRegressionForm",
    titleKey: "HeaderMenu.OrdinaryLeastSquares",
  },
  {
    featureKey: "CorrelationMatrix",
    titleKey: "HeaderMenu.CorrelationMatrix",
  },
  {
    featureKey: "GroupStatistics",
    titleKey: "HeaderMenu.GroupStatistics",
  },
  {
    featureKey: "ChartView",
    titleKey: "HeaderMenu.ChartView",
  },
];
