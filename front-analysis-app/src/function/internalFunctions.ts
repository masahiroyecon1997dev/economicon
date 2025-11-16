import type { TableInfoType } from "../types/commonTypes";
import { fetchDataToJson, getColumnList } from "./restApis";

export const getTableInfo = async (
  tableName: string
): Promise<TableInfoType> => {
  try {
    const resFetchDataToJson = await fetchDataToJson(tableName);
    if (resFetchDataToJson.code !== "OK") {
      throw new Error(resFetchDataToJson.message);
    }
    const data = JSON.parse(resFetchDataToJson.result.data);
    const resColumnList = await getColumnList(tableName);
    if (resColumnList.code !== "OK") {
      throw new Error(resColumnList.message);
    }
    return {
      tableName: tableName,
      columnList: resColumnList.result.columnInfoList,
      isActive: true,
      data: data,
    };
  } catch (error) {
    console.log(error);
    throw error;
  }
};
