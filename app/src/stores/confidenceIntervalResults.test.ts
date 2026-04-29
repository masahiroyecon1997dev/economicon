import type { ConfidenceIntervalResultData } from "@/stores/confidenceIntervalResults";
import { useConfidenceIntervalResultsStore } from "@/stores/confidenceIntervalResults";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------
const makeResult = (
  overrides: Partial<ConfidenceIntervalResultData> = {},
): ConfidenceIntervalResultData => ({
  resultId: "result-001",
  tableName: "sales",
  columnName: "price",
  statistic: { type: "mean", value: 120.5 },
  confidenceInterval: { lower: 115.0, upper: 126.0 },
  confidenceLevel: 0.95,
  ...overrides,
});

// --------------------------------------------------------------------------
// Setup
// --------------------------------------------------------------------------
beforeEach(() => {
  // ストアを初期状態にリセット
  useConfidenceIntervalResultsStore.setState({ results: [] });
});

afterEach(() => {
  vi.restoreAllMocks();
});

// --------------------------------------------------------------------------
// Tests
// --------------------------------------------------------------------------
describe("useConfidenceIntervalResultsStore", () => {
  describe("addResult", () => {
    it("test_addResult_appendsEntryWithResultId", () => {
      const { addResult } = useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());

      const { results } = useConfidenceIntervalResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].resultId).toBe("result-001");
      expect(results[0].tableName).toBe("sales");
      expect(results[0].columnName).toBe("price");
    });

    it("test_addResult_multipleResults_keepsOrder", () => {
      const { addResult } = useConfidenceIntervalResultsStore.getState();
      addResult(makeResult({ resultId: "r1", columnName: "price" }));
      addResult(makeResult({ resultId: "r2", columnName: "quantity" }));

      const { results } = useConfidenceIntervalResultsStore.getState();
      expect(results).toHaveLength(2);
      expect(results[0].columnName).toBe("price");
      expect(results[1].columnName).toBe("quantity");
    });

    it("test_addResult_preservesAllFields", () => {
      const result = makeResult({
        confidenceLevel: 0.99,
        confidenceInterval: { lower: 110.0, upper: 130.0 },
        statistic: { type: "median", value: 118.0 },
      });
      const { addResult } = useConfidenceIntervalResultsStore.getState();
      addResult(result);

      const entry = useConfidenceIntervalResultsStore.getState().results[0];
      expect(entry.confidenceLevel).toBeCloseTo(0.99);
      expect(entry.confidenceInterval.lower).toBeCloseTo(110.0);
      expect(entry.confidenceInterval.upper).toBeCloseTo(130.0);
      expect(entry.statistic.type).toBe("median");
    });
  });

  describe("removeResult", () => {
    it("test_removeResult_removesCorrectEntry", () => {
      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult({ resultId: "r1", columnName: "price" }));
      addResult(makeResult({ resultId: "r2", columnName: "quantity" }));

      removeResult("r1");

      const { results } = useConfidenceIntervalResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].columnName).toBe("quantity");
    });

    it("test_removeResult_unknownId_doesNothing", () => {
      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());

      removeResult("non-existent-id");

      expect(useConfidenceIntervalResultsStore.getState().results).toHaveLength(
        1,
      );
    });

    it("test_removeResult_lastEntry_leavesEmptyArray", () => {
      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());
      removeResult("result-001");

      expect(useConfidenceIntervalResultsStore.getState().results).toHaveLength(
        0,
      );
    });
  });
});
