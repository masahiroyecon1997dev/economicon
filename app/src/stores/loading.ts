import { create } from "zustand";

type LoadingState = {
  isLoading: boolean;
  loadingMessage: string;
};

type LoadingActions = {
  /**
   * ローディングの表示/非表示を設定する。
   * @param isLoading - true: 表示, false: 非表示
   * @param message   - ローディングメッセージ
   * @param delay     - 表示までの遅延 (ms)。この時間内に clearLoading が呼ばれれば
   *                    ローディングは表示されない。デフォルト 400ms = 短時間処理での
   *                    ちらつき防止。即時表示が必要な場合は 0 を明示すること。
   */
  setLoading: (isLoading: boolean, message?: string, delay?: number) => void;
  clearLoading: () => void;
};

type LoadingStore = LoadingState & LoadingActions;

// タイマーは Zustand の state 外で管理 (非シリアライズ値のため)
let _loadingTimer: ReturnType<typeof setTimeout> | null = null;

export const useLoadingStore = create<LoadingStore>((set) => ({
  isLoading: false,
  loadingMessage: "",

  setLoading: (isLoading: boolean, message = "", delay = 400) => {
    // 既存のタイマーをキャンセル
    if (_loadingTimer !== null) {
      clearTimeout(_loadingTimer);
      _loadingTimer = null;
    }

    if (!isLoading || delay === 0) {
      // 非表示 or 遅延なし: 即時反映
      set({ isLoading, loadingMessage: message });
    } else {
      // 遅延あり: delay ms 後にのみ表示
      // clearLoading が先に呼ばれればタイマーがキャンセルされ表示されない
      _loadingTimer = setTimeout(() => {
        _loadingTimer = null;
        set({ isLoading: true, loadingMessage: message });
      }, delay);
    }
  },

  clearLoading: () => {
    // 保留中のタイマーをキャンセル (一瞬で終わった場合は表示しない)
    if (_loadingTimer !== null) {
      clearTimeout(_loadingTimer);
      _loadingTimer = null;
    }
    set({
      isLoading: false,
      loadingMessage: "",
    });
  },
}));
