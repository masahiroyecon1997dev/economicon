/**
 * useConfidenceIntervalSim のテスト
 *
 * - invoke モック経由で result が取得できること（成功時）
 * - API 失敗時に error がセットされること
 * - params 変更時に debounce 後に再フェッチされること
 */
import { getEconomiconAppAPI } from "@/api/endpoints";
import type { ConfidenceIntervalSimRequestBody } from "@/api/model";
import { useConfidenceIntervalSim } from "@/hooks/useConfidenceIntervalSim";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockConfidenceIntervalSim = vi.fn();

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    confidenceIntervalSim: mockConfidenceIntervalSim,
  } as never);
  mockConfidenceIntervalSim.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

const baseParams: ConfidenceIntervalSimRequestBody = {
  ciType: "mean",
  trials: 100,
  sampleSize: 30,
  confidenceLevel: 0.95,
  trueMean: 0.0,
  trueVariance: 1.0,
};

const mockResult = {
  trueValue: 0.0,
  confidenceLevel: 0.95,
  intervals: [
    { lower: -0.3, upper: 0.4, containsTrue: true },
    { lower: 0.1, upper: 0.8, containsTrue: false },
  ],
};

describe("useConfidenceIntervalSim", () => {
  describe("成功時", () => {
    it("test_success_resultIsSet: debounce 後に result がセットされ loading=false になる", async () => {
      mockConfidenceIntervalSim.mockResolvedValueOnce({
        code: "OK",
        result: mockResult,
      });

      const { result } = renderHook(() => useConfidenceIntervalSim(baseParams));

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
      mockConfidenceIntervalSim.mockReturnValueOnce(
        new Promise((r) => {
          resolve = r;
        }),
      );

      const { result } = renderHook(() => useConfidenceIntervalSim(baseParams));

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
      mockConfidenceIntervalSim.mockRejectedValueOnce(
        new Error("Network error"),
      );

      const { result } = renderHook(() => useConfidenceIntervalSim(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.error).not.toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it("test_error_resultNull: エラー時は result が null のまま", async () => {
      mockConfidenceIntervalSim.mockRejectedValueOnce(new Error("fail"));

      const { result } = renderHook(() => useConfidenceIntervalSim(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.result).toBeNull();
    });
  });

  describe("debounce", () => {
    it("test_debounce_notCalledBeforeDelay: 300ms 未満ではまだ呼び出されない", async () => {
      mockConfidenceIntervalSim.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      renderHook(() => useConfidenceIntervalSim(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(299);
        await Promise.resolve();
      });

      expect(mockConfidenceIntervalSim).not.toHaveBeenCalled();
    });

    it("test_debounce_calledAfterDelay: 300ms 後に呼び出される", async () => {
      mockConfidenceIntervalSim.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      renderHook(() => useConfidenceIntervalSim(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockConfidenceIntervalSim).toHaveBeenCalledTimes(1);
    });

    it("test_debounce_cancelsPreviousOnParamChange: params 変更時に前の debounce がキャンセルされ 1 回だけ呼ばれる", async () => {
      mockConfidenceIntervalSim.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      const { rerender } = renderHook(
        (props: ConfidenceIntervalSimRequestBody) =>
          useConfidenceIntervalSim(props),
        { initialProps: baseParams },
      );

      await act(async () => {
        vi.advanceTimersByTime(100);
      });

      rerender({ ...baseParams, trials: 500 });

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockConfidenceIntervalSim).toHaveBeenCalledTimes(1);
      expect(mockConfidenceIntervalSim).toHaveBeenCalledWith(
        expect.objectContaining({ trials: 500 }),
      );
    });
  });
});
