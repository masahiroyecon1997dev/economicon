/**
 * useAsymptoticNormality のテスト
 *
 * - invoke モック経由で result が取得できること（成功時）
 * - API 失敗時に error がセットされること
 * - params 変更時に debounce 後に再フェッチされること
 */
import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AsymptoticNormalityRequestBody } from "@/api/model";
import { useAsymptoticNormality } from "@/hooks/useAsymptoticNormality";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockAsymptoticNormality = vi.fn();

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    asymptoticNormality: mockAsymptoticNormality,
  } as never);
  mockAsymptoticNormality.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

const baseParams: AsymptoticNormalityRequestBody = {
  sampleSize: 100,
  trueBeta: 1.0,
  errorVariance: 1.0,
  errorType: "normal",
  xDistribution: { xMean: 0, xVariance: 1 },
};

const mockResult = {
  betaEstimates: [0.9, 1.0, 1.1, 0.95, 1.05],
  trueBeta: 1.0,
  isAsymptoticallyNormal: true,
  asymptoticMean: 1.0,
  asymptoticVariance: 0.1,
};

describe("useAsymptoticNormality", () => {
  describe("成功時", () => {
    it("test_success_resultIsSet: debounce 後に result がセットされ loading=false になる", async () => {
      mockAsymptoticNormality.mockResolvedValueOnce({
        code: "OK",
        result: mockResult,
      });

      const { result } = renderHook(() => useAsymptoticNormality(baseParams));

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
      mockAsymptoticNormality.mockReturnValueOnce(
        new Promise((r) => {
          resolve = r;
        }),
      );

      const { result } = renderHook(() => useAsymptoticNormality(baseParams));

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
      mockAsymptoticNormality.mockRejectedValueOnce(
        new Error("シミュレーション失敗"),
      );

      const { result } = renderHook(() => useAsymptoticNormality(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.result).toBeNull();
      expect(result.current.error).toBe("シミュレーション失敗");
    });

    it("test_error_resultNull: エラー時は result が null のまま", async () => {
      mockAsymptoticNormality.mockRejectedValueOnce(new Error("接続エラー"));

      const { result } = renderHook(() => useAsymptoticNormality(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(result.current.result).toBeNull();
    });
  });

  describe("debounce", () => {
    it("test_debounce_notCalledBeforeDelay: 300ms 未満ではまだ呼び出されない", async () => {
      mockAsymptoticNormality.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      renderHook(() => useAsymptoticNormality(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(299);
      });

      expect(mockAsymptoticNormality).not.toHaveBeenCalled();
    });

    it("test_debounce_calledAfterDelay: 300ms 後に呼び出される", async () => {
      mockAsymptoticNormality.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      renderHook(() => useAsymptoticNormality(baseParams));

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockAsymptoticNormality).toHaveBeenCalledTimes(1);
    });

    it("test_debounce_cancelsPreviousOnParamChange: params 変更時に前の debounce がキャンセルされ 1 回だけ呼ばれる", async () => {
      mockAsymptoticNormality.mockResolvedValue({
        code: "OK",
        result: mockResult,
      });

      const { rerender } = renderHook(
        (params: AsymptoticNormalityRequestBody) =>
          useAsymptoticNormality(params),
        { initialProps: baseParams },
      );

      await act(async () => {
        vi.advanceTimersByTime(200);
      });

      rerender({ ...baseParams, trueBeta: 2.0 });

      await act(async () => {
        vi.advanceTimersByTime(300);
        await Promise.resolve();
      });

      expect(mockAsymptoticNormality).toHaveBeenCalledTimes(1);
      expect(mockAsymptoticNormality).toHaveBeenCalledWith(
        expect.objectContaining({ trueBeta: 2.0 }),
      );
    });
  });
});
