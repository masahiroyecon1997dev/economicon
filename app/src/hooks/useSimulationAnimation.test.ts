import {
  SPEED_INTERVAL_MS,
  useSimulationAnimation,
} from "@/hooks/useSimulationAnimation";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

describe("useSimulationAnimation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("初期状態", () => {
    it("test_initialState_frame0_notPlaying", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      expect(result.current.frame).toBe(0);
      expect(result.current.playing).toBe(false);
    });
  });

  describe("play", () => {
    it("test_play_advancesFrameByOne", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal);
      });
      expect(result.current.frame).toBe(1);
    });

    it("test_play_advancesMultipleFrames", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 3);
      });
      expect(result.current.frame).toBe(3);
    });

    it("test_play_stopsAtTotalFrames", () => {
      const { result } = renderHook(() => useSimulationAnimation(3, "normal"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 10);
      });
      expect(result.current.frame).toBe(3);
      expect(result.current.playing).toBe(false);
    });

    it("test_play_setsPlayingTrue", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      act(() => {
        result.current.play();
      });
      expect(result.current.playing).toBe(true);
    });

    it("test_play_atEnd_doesNotStartPlaying", () => {
      const { result } = renderHook(() => useSimulationAnimation(2, "normal"));
      // 末尾まで再生
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 5);
      });
      expect(result.current.playing).toBe(false);
      // もう一度 play しても無視される
      act(() => {
        result.current.play();
      });
      expect(result.current.playing).toBe(false);
    });
  });

  describe("pause", () => {
    it("test_pause_stopsPlaying", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 2);
      });
      act(() => {
        result.current.pause();
      });
      expect(result.current.playing).toBe(false);
      const frameAtPause = result.current.frame;
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 5);
      });
      // ポーズ後はフレームが進まない
      expect(result.current.frame).toBe(frameAtPause);
    });
  });

  describe("reset", () => {
    it("test_reset_setsFrame0AndStops", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "normal"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 5);
      });
      act(() => {
        result.current.reset();
      });
      expect(result.current.frame).toBe(0);
      expect(result.current.playing).toBe(false);
    });

    it("test_reset_allowsReplay", () => {
      const { result } = renderHook(() => useSimulationAnimation(2, "normal"));
      // 末尾まで再生
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 5);
      });
      expect(result.current.frame).toBe(2);
      // リセット後に再生できる
      act(() => {
        result.current.reset();
      });
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal);
      });
      expect(result.current.frame).toBe(1);
    });
  });

  describe("totalFrames 変更時リセット", () => {
    it("test_totalFramesChange_resetsState", () => {
      const { result, rerender } = renderHook(
        ({ total }: { total: number }) =>
          useSimulationAnimation(total, "normal"),
        { initialProps: { total: 10 } },
      );
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.normal * 5);
      });
      expect(result.current.frame).toBe(5);
      // totalFrames が変わるとリセット
      act(() => {
        rerender({ total: 20 });
      });
      expect(result.current.frame).toBe(0);
      expect(result.current.playing).toBe(false);
    });
  });

  describe("速度設定", () => {
    it("test_slowSpeed_usesSlowInterval", () => {
      const { result } = renderHook(() => useSimulationAnimation(10, "slow"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.slow);
      });
      expect(result.current.frame).toBe(1);
    });

    it("test_fastSpeed_usesFastInterval", () => {
      const { result } = renderHook(() => useSimulationAnimation(100, "fast"));
      act(() => {
        result.current.play();
      });
      act(() => {
        vi.advanceTimersByTime(SPEED_INTERVAL_MS.fast * 5);
      });
      expect(result.current.frame).toBe(5);
    });
  });
});
