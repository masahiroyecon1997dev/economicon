import { getEconomiconAPI } from "../../api/endpoints";
import type { TableInfoType } from "../../types/commonTypes";

export const getTableInfo = async (
  tableName: string,
  startRow: number = 1,
  fetchRows: number = 100,
): Promise<TableInfoType> => {
  try {
    const api = getEconomiconAPI();
    const resFetchDataToJson = await api.fetchDataToJson({
      tableName,
      startRow,
      fetchRows,
    });
    if (resFetchDataToJson.code !== "OK") {
      throw new Error("データの取得に失敗しました");
    }
    const data = JSON.parse(resFetchDataToJson.result.data);
    const resColumnList = await api.getColumnList({ tableName });
    if (resColumnList.code !== "OK") {
      throw new Error("カラム情報の取得に失敗しました");
    }
    const {
      totalRows,
      startRow: resStartRow,
      endRow,
    } = resFetchDataToJson.result;
    const totalPages = Math.ceil(totalRows / fetchRows);
    const pageIndex = Math.floor((resStartRow - 1) / fetchRows) + 1;

    return {
      tableName: tableName,
      columnList: resColumnList.result.columnInfoList,
      isActive: true,
      data: data,
      startRow: resStartRow,
      endRow: endRow,
      pageIndex: pageIndex,
      totalRows: totalRows,
      totalPages: totalPages,
    };
  } catch (error) {
    console.log(error);
    throw error;
  }
};
