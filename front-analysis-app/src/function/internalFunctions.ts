import type { TableDataType, TableInfoType } from '../types/commonTypes';
import { fetchDataToJson, getColumnInfoList } from './restApis';

export const fetchData = async (
  tableName: string
): Promise<{ tableName: string; data: TableDataType }> => {
  const resFetchDataToJson = await fetchDataToJson(tableName);
  if (resFetchDataToJson.code === 0) {
    const data = JSON.parse(resFetchDataToJson.result.data);
    return { tableName: tableName, data: data };
  }
  return { tableName: '', data: null };
}

export const getTableInfo = async (tableName: string): Promise<TableInfoType> => {
  const data = await fetchData(tableName);
  const columnList = await getColumnInfoList(tableName);
  return {
    tableName: tableName,
    columnList: columnList.result.columnInfoList,
    isActive: true,
    data: data.data,
  };
};
