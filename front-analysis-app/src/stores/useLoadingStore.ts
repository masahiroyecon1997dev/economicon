import { create } from 'zustand';

type LoadingState = {
  isLoading: boolean;
  loadingMessage: string;
};

type LoadingActions = {
  setLoading: (isLoading: boolean, message?: string) => void;
  clearLoading: () => void;
};

type LoadingStore = LoadingState & LoadingActions;

export const useLoadingStore = create<LoadingStore>((set) => ({
  isLoading: false,
  loadingMessage: '',

  setLoading: (isLoading: boolean, message = '') => {
    set({
      isLoading,
      loadingMessage: message
    });
  },

  clearLoading: () => {
    set({
      isLoading: false,
      loadingMessage: ''
    });
  }
}));
