import { useConfirmDialogStore } from "../../stores/confirmDialog";

/**
 * 確認ダイアログを表示する汎用関数
 * @param title メッセージダイアログのタイトル
 * @param message メッセージ
 * @returns Promise<boolean> - OK が押されれば true、キャンセルなら false
 */
export const showConfirmDialog = (
  title: string,
  message: string,
): Promise<boolean> => {
  return useConfirmDialogStore.getState().showConfirmDialog(title, message);
};
