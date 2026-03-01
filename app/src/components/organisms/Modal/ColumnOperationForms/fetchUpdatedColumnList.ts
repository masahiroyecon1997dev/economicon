import { getEconomiconAPI } from "../../../../api/endpoints";
import type { ColumnType } from "../../../../types/commonTypes";

/**
 * 列操作後に最新の columnList を取得して返す
 */
export const fetchUpdatedColumnList = async (
  tableName: string,
): Promise<ColumnType[]> => {
  const response = await getEconomiconAPI().getColumnList({
    tableName,
    isNumberOnly: false,
  });
  if (response.code === "OK") {
    return response.result.columnInfoList;
  }
  throw new Error("Failed to fetch column list");
};
