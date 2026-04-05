import { beforeEach, describe, expect, it } from "vitest";
import type { LinearRegressionResultType } from "../types/commonTypes";
import { useRegressionResultsStore } from "./regressionResults";

const makeResult = (
  overrides: Partial<LinearRegressionResultType> = {},
): LinearRegressionResultType => ({
  resultId: "result-001",
  tableName: "sales",
  dependentVariable: "price",
  explanatoryVariables: ["quantity", "tax"],
  regressionResult: "OLS",
  parameters: [
    {
      variable: "quantity",
      coefficient: 0.5,
      standardError: 0.1,
      pValue: 0.01,
      tValue: 5.0,
      confidenceIntervalLower: 0.3,
      confidenceIntervalUpper: 0.7,
    },
  ],
  modelStatistics: {
    nObservations: 100,
    R2: 0.85,
    adjustedR2: 0.84,
    fValue: 280.0,
    fProbability: 0.0,
  },
  ...overrides,
});

beforeEach(() => {
  useRegressionResultsStore.setState({ results: [] });
});

describe("useRegressionResultsStore", () => {
  describe("addResult", () => {
    it("test_addResult_appendsToEmptyList", () => {
      const { addResult } = useRegressionResultsStore.getState();
      addResult(makeResult());

      const { results } = useRegressionResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].resultId).toBe("result-001");
    });

    it("test_addResult_preservesInsertionOrder", () => {
      const { addResult } = useRegressionResultsStore.getState();
      addResult(makeResult({ resultId: "r1" }));
      addResult(makeResult({ resultId: "r2" }));

      const { results } = useRegressionResultsStore.getState();
      expect(results[0].resultId).toBe("r1");
      expect(results[1].resultId).toBe("r2");
    });

    it("test_addResult_preservesAllFields", () => {
      const result = makeResult({
        dependentVariable: "income",
        explanatoryVariables: ["age", "education"],
      });
      const { addResult } = useRegressionResultsStore.getState();
      addResult(result);

      const entry = useRegressionResultsStore.getState().results[0];
      expect(entry.dependentVariable).toBe("income");
      expect(entry.explanatoryVariables).toEqual(["age", "education"]);
      expect(entry.modelStatistics.R2).toBeCloseTo(0.85);
    });
  });

  describe("removeResult", () => {
    it("test_removeResult_removesCorrectEntry", () => {
      const { addResult, removeResult } = useRegressionResultsStore.getState();
      addResult(makeResult({ resultId: "r1" }));
      addResult(makeResult({ resultId: "r2" }));
      removeResult("r1");

      const { results } = useRegressionResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].resultId).toBe("r2");
    });

    it("test_removeResult_unknownId_doesNothing", () => {
      const { addResult, removeResult } = useRegressionResultsStore.getState();
      addResult(makeResult({ resultId: "r1" }));
      removeResult("nonExistent");

      expect(useRegressionResultsStore.getState().results).toHaveLength(1);
    });

    it("test_removeResult_onEmptyList_doesNothing", () => {
      const { removeResult } = useRegressionResultsStore.getState();
      removeResult("r1");

      expect(useRegressionResultsStore.getState().results).toEqual([]);
    });
  });
});
