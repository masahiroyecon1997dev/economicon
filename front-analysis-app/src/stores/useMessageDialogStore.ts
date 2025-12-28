import { create } from "zustand";

type MessageDialogState = {
  isOpen: boolean;
  title: string;
  message: string;
  resolver: ((value: void) => void) | null;
};

type MessageDialogActions = {
  showMessageDialog: (title: string, message: string) => Promise<void>;
  closeMessageDialog: () => void;
};

type MessageDialogStore = MessageDialogState & MessageDialogActions;

export const useMessageDialogStore = create<MessageDialogStore>((set, get) => ({
  isOpen: false,
  title: "",
  message: "",
  resolver: null,

  showMessageDialog: (title: string, message: string) => {
    return new Promise<void>((resolve) => {
      // 既に開いている場合は前のダイアログを先にクローズ
      const currentState = get();
      if (currentState.resolver) {
        currentState.resolver();
      }

      set({
        isOpen: true,
        title,
        message,
        resolver: resolve,
      });
    });
  },

  closeMessageDialog: () => {
    const { resolver } = get();

    // まず状態をクリア
    set({
      isOpen: false,
      title: "",
      message: "",
      resolver: null,
    });

    // Promiseをresolve（少し遅延を入れてアニメーション完了を待つ）
    if (resolver) {
      setTimeout(() => {
        resolver();
      }, 100);
    }
  },
}));
