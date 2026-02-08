// axiosを廃止し、clientをインポート
import { API_ENDPOINTS } from "../../constants/api";
import type * as apiTypes from "../../types/apiTypes";
import { client } from "./client";

export const getSettings = async (): Promise<apiTypes.ResGetSettingsType> => {
  const response = await client.get<apiTypes.ResGetSettingsType>(
    API_ENDPOINTS.SETTING.GET_SETTINGS,
  );
  return response.data;
};

export const getTableList = async (): Promise<apiTypes.ResgetTableListType> => {
  const response = await client.get<apiTypes.ResgetTableListType>(
    API_ENDPOINTS.TABLE.GET_LIST,
  );
  return response.data;
};

export const getFiles = async (
  path: string,
): Promise<apiTypes.ResGetFilesType> => {
  const response = await client.post<apiTypes.ResGetFilesType>(
    API_ENDPOINTS.FILE.GET_LIST,
    { directoryPath: path },
  );
  return response.data;
};

export const importCsvByPath = async (
  requestBody: apiTypes.ReqImportCsvByPathType,
): Promise<apiTypes.ResImportCsvByPathType> => {
  const response = await client.post<apiTypes.ResImportCsvByPathType>(
    API_ENDPOINTS.DATA.IMPORT_CSV_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importExcelByPath = async (
  requestBody: apiTypes.ReqImportExcelByPathType,
): Promise<apiTypes.ResImportExcelByPathType> => {
  const response = await client.post<apiTypes.ResImportExcelByPathType>(
    API_ENDPOINTS.DATA.IMPORT_EXCEL_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importParquetByPath = async (
  requestBody: apiTypes.ReqImportParquetByPathType,
): Promise<apiTypes.ResImportParquetByPathType> => {
  const response = await client.post<apiTypes.ResImportParquetByPathType>(
    API_ENDPOINTS.DATA.IMPORT_PARQUET_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const getColumnList = async (
  tableName: string,
  isNumberOnly: string = "false",
): Promise<apiTypes.ResGetColumnInfoType> => {
  const response = await client.post<apiTypes.ResGetColumnInfoType>(
    API_ENDPOINTS.COLUMN.GET_LIST,
    {
      tableName: tableName,
      isNumberOnly: isNumberOnly,
    },
  );
  return response.data;
};

export const fetchDataToJson = async (
  tableName: string,
  startRow: number = 0,
  fetchRows: number = 100,
): Promise<apiTypes.ResFetchDataToJsonType> => {
  const response = await client.post<apiTypes.ResFetchDataToJsonType>(
    API_ENDPOINTS.TABLE.FETCH_DATA_TO_JSON,
    {
      tableName: tableName,
      startRow: startRow,
      fetchRows: fetchRows,
    },
  );
  return response.data;
};

export const fetchDataToArrow = async (
  tableName: string,
  startRow: number = 0,
  chunk_size: number = 500,
): Promise<apiTypes.ResFetchDataToArrowType> => {
  const response = await client.fetch_binary<number[]>(
    "POST",
    API_ENDPOINTS.TABLE.FETCH_DATA_TO_ARROW,
    {
      tableName: tableName,
      startRow: startRow,
      chunkSize: chunk_size,
    },
  );
  // Tauriからのバイナリ配列(number[])をUint8Arrayに変換
  return new Uint8Array(response.data);
};

export const createSimulationDataTable = async (
  requestBody: apiTypes.ReqCreateSimulationDataTableType,
): Promise<apiTypes.ResCreateSimulationDataTableType> => {
  const response = await client.post<apiTypes.ResCreateSimulationDataTableType>(
    API_ENDPOINTS.TABLE.CREATE_SIMULATION_DATA,
    requestBody,
  );
  return response.data;
};

export const exportCsvByPath = async (
  requestBody: apiTypes.ReqExportCsvByPathType,
): Promise<apiTypes.ResExportCsvByPathType> => {
  const response = await client.post<apiTypes.ResExportCsvByPathType>(
    API_ENDPOINTS.DATA.EXPORT_CSV_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const exportExcelByPath = async (
  requestBody: apiTypes.ReqExportExcelByPathType,
): Promise<apiTypes.ResExportExcelByPathType> => {
  const response = await client.post<apiTypes.ResExportExcelByPathType>(
    API_ENDPOINTS.DATA.EXPORT_EXCEL_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const exportParquetByPath = async (
  requestBody: apiTypes.ReqExportParquetByPathType,
): Promise<apiTypes.ResExportParquetByPathType> => {
  const response = await client.post<apiTypes.ResExportParquetByPathType>(
    API_ENDPOINTS.DATA.EXPORT_PARQUET_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importCsv = async (
  file: File,
): Promise<apiTypes.ResImportCsvType> => {
  // FormDataの作成は不要になり、client.uploadを使用
  const response = await client.upload<apiTypes.ResImportCsvType>(
    API_ENDPOINTS.DATA.IMPORT_CSV_BY_FILE,
    file,
  );
  return response.data;
};

export const calculateColumn = async (
  requestBody: apiTypes.ReqCalculateColumnType,
): Promise<apiTypes.ResCalculateColumnType> => {
  const response = await client.post<apiTypes.ResCalculateColumnType>(
    API_ENDPOINTS.COLUMN.CALCULATE,
    requestBody,
  );
  return response.data;
};

export const linearRegression = async (
  requestBody: apiTypes.ReqLinearRegressionType,
): Promise<apiTypes.ResLinearRegressionType> => {
  const response = await client.post<apiTypes.ResLinearRegressionType>(
    API_ENDPOINTS.REGRESSION.LINEAR,
    requestBody,
  );
  return response.data;
};
