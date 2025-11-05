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
    set({
      isOpen: false,
      title: '',
      message: '',
      resolver: null,
    });
    if (resolver) {
      resolver();
    }
  },
}));
