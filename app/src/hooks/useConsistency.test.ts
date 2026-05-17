/**
 * useConsistency のテスト
 *
 * - invoke モック経由で result が取得できること（成功時）
 * - API 失敗時に error がセットされること
 * - params 変更時に debounce 後に再フェッチされること
 */
import { getEconomiconAppAPI } from "@/api/endpoints";
import type { ConsistencyRequestBody } from "@/api/model";
import { useConsistency } from "@/hooks/useConsistency";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockConsistency = vi.fn();

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    consistency: mockConsistency,
  } as never);
  mockConsistency.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

const baseParams: ConsistencyRequestBody = {
  nMax: 500,
  trueBeta: 1.0,
  errorVariance: 1.0,
  endogenous: false,
  xDistribution: { xMean: 0, xVariance: 1 },
};

const mockResult = {
  nValues: [10, 20, 50, 100, 200, 500],
  betaEstimates: [1.2, 1.1, 1.05, 1.02, 1.01, 1.0],
  trueBeta: 1.0,
  probabilityLimit: 1.0,
};

describe("useConsistency", () => {
  describe("成功時", () => {
    it("test_success_resultIsSet: debounce 後に result がセットされ loading=false になる", async () => {
      mockConsistency.mockResolvedValueOnce({
        code: "OK",
        result: mockResult,
      });

      const { result } = renderHook(() => useConsistency(baseParams));

      expect(result.current.loading).toBe(false);
      expect(result.current.result).toBeNull();

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.result).toEqual(mockResult);
      expect(result.current.error).toBeNull();
    });

    it("test_loading_trueWhileFetching: フェッチ中は loading=true になる", async () => {
      let resolve!: (v: unknown) => void;
      mockConsistency.mockReturnValueOnce(
        new Promise((r) => {
          resolve = r;
        }),
      );

      const { result } = renderHook(() => useConsistency(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolve({ code: "OK", result: mockResult });
        await Promise.resolve();
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe("エラー時", () => {
    it("test_error_isSet: API 失敗時に error がセットされる", async () => {
      mockConsistency.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useConsistency(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it("test_error_resultNull: エラー時は result が null のまま", async () => {
      mockConsistency.mockRejectedValueOnce(new Error("fail"));

      const { result } = renderHook(() => useConsistency(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.result).toBeNull();
    });
  });

  describe("debounce", () => {
    it("test_debounce_notCalledBeforeDelay: 300ms 未満ではまだ呼び出されない", async () => {
      mockConsistency.mockResolvedValue({ code: "OK", result: mockResult });

      renderHook(() => useConsistency(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(299);
        await Promise.resolve();
      });

      expect(mockConsistency).not.toHaveBeenCalled();
    });

    it("test_debounce_calledAfterDelay: 300ms 後に呼び出される", async () => {
      mockConsistency.mockResolvedValue({ code: "OK", result: mockResult });

      renderHook(() => useConsistency(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockConsistency).toHaveBeenCalledTimes(1);
    });

    it("test_debounce_cancelsPreviousOnParamChange: params 変更時に前の debounce がキャンセルされ 1 回だけ呼ばれる", async () => {
      mockConsistency.mockResolvedValue({ code: "OK", result: mockResult });

      const { rerender } = renderHook(
        (props: ConsistencyRequestBody) => useConsistency(props),
        { initialProps: baseParams },
      );

      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      rerender({ ...baseParams, nMax: 1000 });

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockConsistency).toHaveBeenCalledTimes(1);
      expect(mockConsistency).toHaveBeenCalledWith(
        expect.objectContaining({ nMax: 1000 }),
      );
    });
  });
});
