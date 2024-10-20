import { TableDataType, TableInfoType } from "../types/commonTypes";
import { fetchDataToJson, getColumnNameList } from "./restApis";

export async function fetchData(tableName: string): Promise<{ tableName: string, data: TableDataType }> {
  const resFetchDataToJson = await fetchDataToJson(tableName);
  if (resFetchDataToJson.code === 0) {
    const data = JSON.parse(resFetchDataToJson.result.data);
    return {tableName: tableName, data: data};
  }
  return {tableName: '', data: null};
}

export async function getTableInfo(tableName: string): Promise<TableInfoType> {
  const data = await fetchData(tableName);
  const columnList = await getColumnNameList(tableName);
  return {tableName: tableName, columnNameList: columnList.result.columnNameList, isActive: true, data: data.data};
}
