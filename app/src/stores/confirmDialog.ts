import { create } from "zustand";

type ConfirmDialogState = {
  isOpen: boolean;
  title: string;
  message: string;
  resolver: ((value: boolean) => void) | null;
};

type ConfirmDialogActions = {
  showConfirmDialog: (title: string, message: string) => Promise<boolean>;
  confirmDialog: () => void;
  cancelDialog: () => void;
};

type ConfirmDialogStore = ConfirmDialogState & ConfirmDialogActions;

export const useConfirmDialogStore = create<ConfirmDialogStore>((set, get) => ({
  isOpen: false,
  title: "",
  message: "",
  resolver: null,

  showConfirmDialog: (title: string, message: string) => {
    return new Promise<boolean>((resolve) => {
      // 既に開いている場合は前のダイアログを先にキャンセル扱いでクローズ
      const currentState = get();
      if (currentState.resolver) {
        currentState.resolver(false);
      }

      set({
        isOpen: true,
        title,
        message,
        resolver: resolve,
      });
    });
  },

  confirmDialog: () => {
    const { resolver } = get();

    set({
      isOpen: false,
      title: "",
      message: "",
      resolver: null,
    });

    if (resolver) {
      setTimeout(() => {
        resolver(true);
      }, 100);
    }
  },

  cancelDialog: () => {
    const { resolver } = get();

    set({
      isOpen: false,
      title: "",
      message: "",
      resolver: null,
    });

    if (resolver) {
      setTimeout(() => {
        resolver(false);
      }, 100);
    }
  },
}));
