import type { ColumnType } from "../../../../types/commonTypes";

/**
 * 列操作フォームの共通 Props 型
 */
export type ColumnOperationFormPropsType = {
  tableName: string;
  column: ColumnType;
  /** 操作成功時に最新の columnList を渡してコールバック */
  onSuccess: (updatedColumnList: ColumnType[]) => void;
  onClose: () => void;
};
