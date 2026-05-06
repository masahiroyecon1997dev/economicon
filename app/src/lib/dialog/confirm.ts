import {
  type ShowConfirmDialogOptionsType,
  useConfirmDialogStore,
} from "@/stores/confirmDialog";

/**
 * 確認ダイアログを表示する汎用関数
 * @param title メッセージダイアログのタイトル
 * @param message メッセージ
 * @returns Promise<boolean> - OK が押されれば true、キャンセルなら false
 */
export const showConfirmDialog = (
  title: string,
  message: string,
  options?: ShowConfirmDialogOptionsType,
): Promise<boolean> => {
  return useConfirmDialogStore
    .getState()
    .showConfirmDialog(title, message, options);
};
