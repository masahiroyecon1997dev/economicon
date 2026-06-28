import { create } from "zustand";

type ExplainerDialogStore = {
  key: string | null;
  triggerRect: DOMRect | null;
  open: (key: string, triggerRect?: DOMRect) => void;
  close: () => void;
};

export const useExplainerDialogStore = create<ExplainerDialogStore>((set) => ({
  key: null,
  triggerRect: null,
  open: (key, triggerRect) => set({ key, triggerRect: triggerRect ?? null }),
  close: () => set({ key: null, triggerRect: null }),
}));

/** 任意の場所から命令的に解説ダイアログを開く */
export const openExplainerDialog = (
  key: string,
  triggerRect?: DOMRect,
): void => {
  useExplainerDialogStore.getState().open(key, triggerRect);
};
