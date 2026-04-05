import type { ConfidenceIntervalResultData } from "@/stores/confidenceIntervalResults";
import { useConfidenceIntervalResultsStore } from "@/stores/confidenceIntervalResults";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------
const makeResult = (
  overrides: Partial<ConfidenceIntervalResultData> = {},
): ConfidenceIntervalResultData => ({
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
    it("test_addResult_appendsEntryWithId", () => {
      vi.spyOn(crypto, "randomUUID").mockReturnValueOnce(
        "00000000-0000-0000-0000-000000000001",
      );
      const { addResult } = useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());

      const { results } = useConfidenceIntervalResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe("00000000-0000-0000-0000-000000000001");
      expect(results[0].tableName).toBe("sales");
      expect(results[0].columnName).toBe("price");
    });

    it("test_addResult_multipleResults_keepsOrder", () => {
      vi.spyOn(crypto, "randomUUID")
        .mockReturnValueOnce("00000000-0000-0000-0000-000000000001")
        .mockReturnValueOnce("00000000-0000-0000-0000-000000000002");

      const { addResult } = useConfidenceIntervalResultsStore.getState();
      addResult(makeResult({ columnName: "price" }));
      addResult(makeResult({ columnName: "quantity" }));

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
      vi.spyOn(crypto, "randomUUID")
        .mockReturnValueOnce("00000000-0000-0000-0000-000000000001")
        .mockReturnValueOnce("00000000-0000-0000-0000-000000000002");

      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult({ columnName: "price" }));
      addResult(makeResult({ columnName: "quantity" }));

      removeResult("00000000-0000-0000-0000-000000000001");

      const { results } = useConfidenceIntervalResultsStore.getState();
      expect(results).toHaveLength(1);
      expect(results[0].columnName).toBe("quantity");
    });

    it("test_removeResult_unknownId_doesNothing", () => {
      vi.spyOn(crypto, "randomUUID").mockReturnValueOnce(
        "00000000-0000-0000-0000-000000000001",
      );
      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());

      removeResult("non-existent-id");

      expect(useConfidenceIntervalResultsStore.getState().results).toHaveLength(
        1,
      );
    });

    it("test_removeResult_lastEntry_leavesEmptyArray", () => {
      vi.spyOn(crypto, "randomUUID").mockReturnValueOnce(
        "00000000-0000-0000-0000-000000000001",
      );
      const { addResult, removeResult } =
        useConfidenceIntervalResultsStore.getState();
      addResult(makeResult());
      removeResult("00000000-0000-0000-0000-000000000001");

      expect(useConfidenceIntervalResultsStore.getState().results).toHaveLength(
        0,
      );
    });
  });
});
