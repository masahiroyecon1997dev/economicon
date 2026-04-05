import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useConfirmDialogStore } from "./confirmDialog";

beforeEach(() => {
  vi.useFakeTimers();
  useConfirmDialogStore.setState({
    isOpen: false,
    title: "",
    message: "",
    resolver: null,
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useConfirmDialogStore", () => {
  describe("showConfirmDialog", () => {
    it("test_showConfirmDialog_opensDialogWithTitleAndMessage", () => {
      const { showConfirmDialog } = useConfirmDialogStore.getState();
      void showConfirmDialog("確認", "削除しますか？");

      const state = useConfirmDialogStore.getState();
      expect(state.isOpen).toBe(true);
      expect(state.title).toBe("確認");
      expect(state.message).toBe("削除しますか？");
      expect(state.resolver).not.toBeNull();
    });

    it("test_showConfirmDialog_returnsPromise", () => {
      const { showConfirmDialog } = useConfirmDialogStore.getState();
      const promise = showConfirmDialog("T", "M");
      expect(promise).toBeInstanceOf(Promise);
    });

    it("test_showConfirmDialog_existingResolver_cancelledWithFalse", async () => {
      const { showConfirmDialog } = useConfirmDialogStore.getState();
      const firstPromise = showConfirmDialog("First", "First message");

      // 2つ目を開く → 1つ目は false で即解決
      showConfirmDialog("Second", "Second message");

      const firstResult = await firstPromise;
      expect(firstResult).toBe(false);
    });
  });

  describe("confirmDialog", () => {
    it("test_confirmDialog_resolvesPromiseWithTrue", async () => {
      const { showConfirmDialog, confirmDialog } =
        useConfirmDialogStore.getState();
      const promise = showConfirmDialog("確認", "OK?");

      confirmDialog();
      vi.advanceTimersByTime(200);

      const result = await promise;
      expect(result).toBe(true);
    });

    it("test_confirmDialog_closesDialog", () => {
      const { showConfirmDialog, confirmDialog } =
        useConfirmDialogStore.getState();
      void showConfirmDialog("T", "M");
      confirmDialog();

      const state = useConfirmDialogStore.getState();
      expect(state.isOpen).toBe(false);
      expect(state.resolver).toBeNull();
    });

    it("test_confirmDialog_noResolver_doesNotThrow", () => {
      const { confirmDialog } = useConfirmDialogStore.getState();
      expect(() => confirmDialog()).not.toThrow();
    });
  });

  describe("cancelDialog", () => {
    it("test_cancelDialog_resolvesPromiseWithFalse", async () => {
      const { showConfirmDialog, cancelDialog } =
        useConfirmDialogStore.getState();
      const promise = showConfirmDialog("確認", "Cancel?");

      cancelDialog();
      vi.advanceTimersByTime(200);

      const result = await promise;
      expect(result).toBe(false);
    });

    it("test_cancelDialog_closesDialog", () => {
      const { showConfirmDialog, cancelDialog } =
        useConfirmDialogStore.getState();
      void showConfirmDialog("T", "M");
      cancelDialog();

      const state = useConfirmDialogStore.getState();
      expect(state.isOpen).toBe(false);
      expect(state.resolver).toBeNull();
    });

    it("test_cancelDialog_noResolver_doesNotThrow", () => {
      const { cancelDialog } = useConfirmDialogStore.getState();
      expect(() => cancelDialog()).not.toThrow();
    });
  });
});
