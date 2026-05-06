import {
  LOADING_MIN_DURATION,
  _resetLoadingTimers,
  useLoadingStore,
} from "@/stores/loading";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.useFakeTimers();
  // vi.useFakeTimers() で時刻コンテキストが切り替わるため
  // モジュールレベルの _showTime 等を明示的にリセットする
  _resetLoadingTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useLoadingStore", () => {
  describe("setLoading — 即時表示 (delay=0)", () => {
    it("test_setLoading_delay0_showsImmediately", () => {
      const { setLoading } = useLoadingStore.getState();
      setLoading(true, "処理中...", 0);

      const state = useLoadingStore.getState();
      expect(state.isLoading).toBe(true);
      expect(state.loadingMessage).toBe("処理中...");
    });

    it("test_setLoading_false_delay0_hidesImmediately", () => {
      useLoadingStore.setState({ isLoading: true, loadingMessage: "loading" });
      const { setLoading } = useLoadingStore.getState();
      setLoading(false, "", 0);

      expect(useLoadingStore.getState().isLoading).toBe(false);
    });
  });

  describe("setLoading — 遅延表示 (delay>0)", () => {
    it("test_setLoading_withDelay_doesNotShowBeforeTimeout", () => {
      const { setLoading } = useLoadingStore.getState();
      setLoading(true, "処理中...", 400);

      // タイマー発火前はまだ非表示
      expect(useLoadingStore.getState().isLoading).toBe(false);
    });

    it("test_setLoading_withDelay_showsAfterTimeout", () => {
      const { setLoading } = useLoadingStore.getState();
      setLoading(true, "処理中...", 400);
      vi.advanceTimersByTime(400);

      expect(useLoadingStore.getState().isLoading).toBe(true);
      expect(useLoadingStore.getState().loadingMessage).toBe("処理中...");
    });

    it("test_setLoading_defaultDelay_is400ms", () => {
      const { setLoading } = useLoadingStore.getState();
      setLoading(true, "msg");

      vi.advanceTimersByTime(399);
      expect(useLoadingStore.getState().isLoading).toBe(false);

      vi.advanceTimersByTime(1);
      expect(useLoadingStore.getState().isLoading).toBe(true);
    });

    it("test_setLoading_secondCallCancelsFirstTimer", () => {
      const { setLoading } = useLoadingStore.getState();
      setLoading(true, "first", 400);
      // 200ms 後に別のメッセージで上書き
      vi.advanceTimersByTime(200);
      setLoading(true, "second", 400);
      vi.advanceTimersByTime(400);

      // second のタイマーが発火、first は既にキャンセル済み
      expect(useLoadingStore.getState().loadingMessage).toBe("second");
    });
  });

  describe("clearLoading", () => {
    it("test_clearLoading_hidesLoadingAndClearsMessage", () => {
      useLoadingStore.setState({ isLoading: true, loadingMessage: "busy" });
      const { clearLoading } = useLoadingStore.getState();
      clearLoading();

      const state = useLoadingStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.loadingMessage).toBe("");
    });

    it("test_clearLoading_cancelsPendingTimer", () => {
      const { setLoading, clearLoading } = useLoadingStore.getState();
      setLoading(true, "msg", 400);
      clearLoading(); // タイマーキャンセル

      vi.advanceTimersByTime(400);
      // タイマーがキャンセルされているため表示されない
      expect(useLoadingStore.getState().isLoading).toBe(false);
    });
  });

  describe("clearLoading — 最小表示時間 (LOADING_MIN_DURATION)", () => {
    it("test_clearLoading_minDuration_delaysHide_whenLoadingJustShown", () => {
      const { setLoading, clearLoading } = useLoadingStore.getState();
      setLoading(true, "msg", 0); // 即時表示 (_showTime セット)

      // すぐに clearLoading → MIN_DURATION が残っているため即時非表示にならない
      clearLoading();
      expect(useLoadingStore.getState().isLoading).toBe(true);

      // MIN_DURATION 経過後に非表示
      vi.advanceTimersByTime(LOADING_MIN_DURATION);
      expect(useLoadingStore.getState().isLoading).toBe(false);
    });

    it("test_clearLoading_minDuration_hidesImmediately_whenDurationElapsed", () => {
      const { setLoading, clearLoading } = useLoadingStore.getState();
      setLoading(true, "msg", 0);

      // MIN_DURATION 以上経過してから clearLoading
      vi.advanceTimersByTime(LOADING_MIN_DURATION);
      clearLoading();

      expect(useLoadingStore.getState().isLoading).toBe(false);
    });

    it("test_clearLoading_minDuration_notApplied_whenNeverShown", () => {
      const { setLoading, clearLoading } = useLoadingStore.getState();
      // delay=400 でまだ表示されていない状態
      setLoading(true, "msg", 400);

      // タイマー発火前に clearLoading → 最小表示時間は適用しない
      clearLoading();
      expect(useLoadingStore.getState().isLoading).toBe(false);

      // 400ms 経過しても表示されない
      vi.advanceTimersByTime(400);
      expect(useLoadingStore.getState().isLoading).toBe(false);
    });
  });
});
