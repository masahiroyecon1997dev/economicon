import { getEconomiconAppAPI } from "@/api/endpoints";
import type { TableInfoType } from "@/types/commonTypes";

/**
 * テーブルメタ情報を取得する（軽量版）。
 *
 * columnList のみ API から取得し、totalRows は 0 で初期化する。
 * 実際の totalRows は VirtualTable の初回チャンクフェッチ後に
 * Arrow スキーマメタデータから自動更新される。
 */
export const getTableInfo = async (
  tableName: string,
): Promise<TableInfoType> => {
  const api = getEconomiconAppAPI();
  const resColumnList = await api.getColumnList({ tableName });
  if (resColumnList.code !== "OK") {
    throw new Error("カラム情報の取得に失敗しました");
  }
  return {
    tableName,
    columnList: resColumnList.result.columnInfoList,
    totalRows: 0, // VirtualTable 初回フェッチで Arrow メタデータから更新
    isActive: true,
  };
};
