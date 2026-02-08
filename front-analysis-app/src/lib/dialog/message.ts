import { useMessageDialogStore } from "../../stores/useMessageDialogStore";

/**
 * メッセージダイアログを表示する汎用関数
 * @param title メッセージダイアログのタイトル
 * @param message メッセージ
 * @returns Promise<void> - OKボタンが押されるまで待機
 */
export const showMessageDialog = (
  title: string,
  message: string,
): Promise<void> => {
  return useMessageDialogStore.getState().showMessageDialog(title, message);
};

/**
 * メッセージダイアログを閉じる関数
 */
export const closeMessageDialog = (): void => {
  useMessageDialogStore.getState().closeMessageDialog();
};
