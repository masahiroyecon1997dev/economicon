import { create } from 'zustand';

type ErrorDialogState = {
  isOpen: boolean;
  title: string;
  message: string;
  resolver: ((value: void) => void) | null;
};

type ErrorDialogActions = {
  showErrorDialog: (title: string, message: string) => Promise<void>;
  closeErrorDialog: () => void;
};

type ErrorDialogStore = ErrorDialogState & ErrorDialogActions;

export const useErrorDialogStore = create<ErrorDialogStore>((set, get) => ({
  isOpen: false,
  title: '',
  message: '',
  resolver: null,

  showErrorDialog: (title: string, message: string) => {
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

  closeErrorDialog: () => {
    const { resolver } = get();

    // まず状態をクリア
    set({
      isOpen: false,
      title: '',
      message: '',
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
