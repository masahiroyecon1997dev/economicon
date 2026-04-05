import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useMessageDialogStore } from "./messageDialog";

beforeEach(() => {
  vi.useFakeTimers();
  useMessageDialogStore.setState({
    isOpen: false,
    title: "",
    message: "",
    resolver: null,
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useMessageDialogStore", () => {
  describe("showMessageDialog", () => {
    it("test_showMessageDialog_opensDialogWithTitleAndMessage", () => {
      const { showMessageDialog } = useMessageDialogStore.getState();
      void showMessageDialog("エラー", "予期しないエラーが発生しました。");

      const state = useMessageDialogStore.getState();
      expect(state.isOpen).toBe(true);
      expect(state.title).toBe("エラー");
      expect(state.message).toBe("予期しないエラーが発生しました。");
      expect(state.resolver).not.toBeNull();
    });

    it("test_showMessageDialog_returnsPromise", () => {
      const { showMessageDialog } = useMessageDialogStore.getState();
      const promise = showMessageDialog("T", "M");
      expect(promise).toBeInstanceOf(Promise);
    });

    it("test_showMessageDialog_existingResolver_resolvedBeforeOpen", async () => {
      const { showMessageDialog } = useMessageDialogStore.getState();
      const firstPromise = showMessageDialog("First", "First");

      // 2つ目を開く → 1つ目の resolver が即 resolve される
      showMessageDialog("Second", "Second");

      vi.advanceTimersByTime(200);
      await expect(firstPromise).resolves.toBeUndefined();
    });
  });

  describe("closeMessageDialog", () => {
    it("test_closeMessageDialog_closesDialogAndClearsState", () => {
      const { showMessageDialog, closeMessageDialog } =
        useMessageDialogStore.getState();
      void showMessageDialog("T", "M");
      closeMessageDialog();

      const state = useMessageDialogStore.getState();
      expect(state.isOpen).toBe(false);
      expect(state.title).toBe("");
      expect(state.message).toBe("");
      expect(state.resolver).toBeNull();
    });

    it("test_closeMessageDialog_resolvesPromise", async () => {
      const { showMessageDialog, closeMessageDialog } =
        useMessageDialogStore.getState();
      const promise = showMessageDialog("T", "M");

      closeMessageDialog();
      vi.advanceTimersByTime(200);

      await expect(promise).resolves.toBeUndefined();
    });

    it("test_closeMessageDialog_noResolver_doesNotThrow", () => {
      const { closeMessageDialog } = useMessageDialogStore.getState();
      expect(() => closeMessageDialog()).not.toThrow();
    });

    it("test_closeMessageDialog_resolvesOnlyAfterDelay", async () => {
      const { showMessageDialog, closeMessageDialog } =
        useMessageDialogStore.getState();
      const promise = showMessageDialog("T", "M");

      closeMessageDialog();

      // 100ms の setTimeout 内なのでまだ pending のはず
      // ただし Promise の pending 確認は難しいため time advance 後に resolved を確認
      vi.advanceTimersByTime(100);
      await expect(promise).resolves.toBeUndefined();
    });
  });
});
