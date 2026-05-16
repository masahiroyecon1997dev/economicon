import type { ColumnType } from "@/types/commonTypes";

/**
 * 列操作フォームの共通 Props 型
 *
 * - formId: BaseDialog との HTML5 フォーム関連付けに使用
 * - onIsSubmittingChange: 送信中フラグを親ダイアログへ伝達し、フッターボタンを制御する
 * - onClose は削除（キャンセルは BaseDialog 側が管理）
 */
export type ColumnOperationFormPropsType = {
  tableName: string;
  column: ColumnType;
  /** HTML5 フォーム関連付け用 ID */
  formId: string;
  /** 送信中フラグを親ダイアログへ伝達 */
  onIsSubmittingChange: (isSubmitting: boolean) => void;
  /** 操作成功時に最新の columnList を渡してコールバック */
  onSuccess: (updatedColumnList: ColumnType[]) => void;
};
