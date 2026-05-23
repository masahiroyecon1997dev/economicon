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
   *                    ローディングは表示されない。デフォルト LOADING_DELAY_DEFAULT。
   *                    即時表示が必要な場合は 0 を明示すること。
   */
  setLoading: (isLoading: boolean, message?: string, delay?: number) => void;
  clearLoading: () => void;
};

type LoadingStore = LoadingState & LoadingActions;

/** デフォルト表示遅延 (ms): 短時間処理のちらつき防止 */
export const LOADING_DELAY_DEFAULT = 400;
/** ディレクトリ変更などの即レスポンス操作向け短い遅延 (ms) */
export const LOADING_DELAY_DIR = 200;
/** 一度表示されたら最低この時間 (ms) は維持する */
export const LOADING_MIN_DURATION = 300;

// タイマーは Zustand の state 外で管理 (非シリアライズ値のため)
let _showTimer: ReturnType<typeof setTimeout> | null = null; // show delay timer
let _hideTimer: ReturnType<typeof setTimeout> | null = null; // min-duration delay before hide
let _showTime: number | null = null; // when loading was actually shown

export const useLoadingStore = create<LoadingStore>((set) => ({
  isLoading: false,
  loadingMessage: "",

  setLoading: (
    isLoading: boolean,
    message = "",
    delay = LOADING_DELAY_DEFAULT,
  ) => {
    // 既存のタイマーをすべてキャンセル
    if (_showTimer !== null) {
      clearTimeout(_showTimer);
      _showTimer = null;
    }
    if (_hideTimer !== null) {
      clearTimeout(_hideTimer);
      _hideTimer = null;
    }

    if (!isLoading) {
      // 直接非表示（force hide）
      _showTime = null;
      set({ isLoading: false, loadingMessage: message });
    } else if (delay === 0) {
      // 遅延なし: 即時表示
      _showTime = Date.now();
      set({ isLoading: true, loadingMessage: message });
    } else {
      // 遅延あり: delay ms 後にのみ表示
      // clearLoading が先に呼ばれれば _showTimer がキャンセルされ表示されない
      _showTimer = setTimeout(() => {
        _showTimer = null;
        _showTime = Date.now();
        set({ isLoading: true, loadingMessage: message });
      }, delay);
    }
  },

  clearLoading: () => {
    // 保留中の show タイマーをキャンセル (まだ表示されていない)
    if (_showTimer !== null) {
      clearTimeout(_showTimer);
      _showTimer = null;
      _showTime = null;
      set({ isLoading: false, loadingMessage: "" });
      return;
    }

    // 保留中の hide タイマーを再評価のためキャンセル
    if (_hideTimer !== null) {
      clearTimeout(_hideTimer);
      _hideTimer = null;
    }

    // 最小表示時間チェック: 表示開始から LOADING_MIN_DURATION ms 未満ならまだ隠さない
    const elapsed = _showTime !== null ? Date.now() - _showTime : Infinity;
    const remaining = LOADING_MIN_DURATION - elapsed;
    if (remaining > 0) {
      _hideTimer = setTimeout(() => {
        _hideTimer = null;
        _showTime = null;
        set({ isLoading: false, loadingMessage: "" });
      }, remaining);
    } else {
      _showTime = null;
      set({ isLoading: false, loadingMessage: "" });
    }
  },
}));

/**
 * @internal テスト専用: モジュールレベルのタイマー状態とストア状態を完全にリセットする。
 * vi.useFakeTimers() で時刻コンテキストが切り替わると _showTime が stale になるため
 * beforeEach で呼び出すこと。
 */
export const _resetLoadingTimers = () => {
  if (_showTimer !== null) {
    clearTimeout(_showTimer);
    _showTimer = null;
  }
  if (_hideTimer !== null) {
    clearTimeout(_hideTimer);
    _hideTimer = null;
  }
  _showTime = null;
  useLoadingStore.setState({ isLoading: false, loadingMessage: "" });
};
