import { useErrorDialogStore } from '../stores/useErrorDialogStore';

/**
 * エラーダイアログを表示する汎用関数
 * @param title エラーダイアログのタイトル
 * @param message エラーメッセージ
 * @returns Promise<void> - OKボタンが押されるまで待機
 */
export const showErrorDialog = (title: string, message: string): Promise<void> => {
  return useErrorDialogStore.getState().showErrorDialog(title, message);
};

/**
 * エラーダイアログを閉じる関数
 */
export const closeErrorDialog = (): void => {
  useErrorDialogStore.getState().closeErrorDialog();
};
