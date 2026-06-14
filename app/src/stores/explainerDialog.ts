import { create } from "zustand";

type ExplainerDialogStore = {
  key: string | null;
  open: (key: string) => void;
  close: () => void;
};

export const useExplainerDialogStore = create<ExplainerDialogStore>((set) => ({
  key: null,
  open: (key) => set({ key }),
  close: () => set({ key: null }),
}));

/** 任意の場所から命令的に解説ダイアログを開く */
export const openExplainerDialog = (key: string): void => {
  useExplainerDialogStore.getState().open(key);
};
