/**
 * useUnbiasedness のテスト
 *
 * - invoke モック経由で result が取得できること（成功時）
 * - API 失敗時に error がセットされること
 * - params 変更時に debounce 後に再フェッチされること
 */
import { getEconomiconAppAPI } from "@/api/endpoints";
import type { UnbiasednessRequestBody } from "@/api/model";
import { useUnbiasedness } from "@/hooks/useUnbiasedness";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockUnbiasedness = vi.fn();

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    unbiasedness: mockUnbiasedness,
  } as never);
  mockUnbiasedness.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

const baseParams: UnbiasednessRequestBody = {
  numTrials: 200,
  sampleSize: 50,
  trueBeta: 1.0,
  errorVariance: 1.0,
  xDistribution: { xMean: 0, xVariance: 1 },
};

const mockResult = {
  betaEstimates: [0.95, 1.0, 1.05, 0.98, 1.02, 0.99, 1.01],
  trueBeta: 1.0,
};

describe("useUnbiasedness", () => {
  describe("成功時", () => {
    it("test_success_resultIsSet: debounce 後に result がセットされ loading=false になる", async () => {
      mockUnbiasedness.mockResolvedValueOnce({
        code: "OK",
        result: mockResult,
      });

      const { result } = renderHook(() => useUnbiasedness(baseParams));

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
      mockUnbiasedness.mockReturnValueOnce(
        new Promise((r) => {
          resolve = r;
        }),
      );

      const { result } = renderHook(() => useUnbiasedness(baseParams));

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
      mockUnbiasedness.mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useUnbiasedness(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it("test_error_resultNull: エラー時は result が null のまま", async () => {
      mockUnbiasedness.mockRejectedValueOnce(new Error("fail"));

      const { result } = renderHook(() => useUnbiasedness(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.result).toBeNull();
    });
  });

  describe("debounce", () => {
    it("test_debounce_notCalledBeforeDelay: 300ms 未満ではまだ呼び出されない", async () => {
      mockUnbiasedness.mockResolvedValue({ code: "OK", result: mockResult });

      renderHook(() => useUnbiasedness(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(299);
        await Promise.resolve();
      });

      expect(mockUnbiasedness).not.toHaveBeenCalled();
    });

    it("test_debounce_calledAfterDelay: 300ms 後に呼び出される", async () => {
      mockUnbiasedness.mockResolvedValue({ code: "OK", result: mockResult });

      renderHook(() => useUnbiasedness(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockUnbiasedness).toHaveBeenCalledTimes(1);
    });

    it("test_debounce_cancelsPreviousOnParamChange: params 変更時に前の debounce がキャンセルされ 1 回だけ呼ばれる", async () => {
      mockUnbiasedness.mockResolvedValue({ code: "OK", result: mockResult });

      const { rerender } = renderHook(
        (props: UnbiasednessRequestBody) => useUnbiasedness(props),
        { initialProps: baseParams },
      );

      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      rerender({ ...baseParams, numTrials: 500 });

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockUnbiasedness).toHaveBeenCalledTimes(1);
      expect(mockUnbiasedness).toHaveBeenCalledWith(
        expect.objectContaining({ numTrials: 500 }),
      );
    });
  });
});
