import axios from "../configs/axios";
import { API_ENDPOINTS } from "../constants/requests";
import type * as apiTypes from "../types/apiTypes";

export const getSettings = async (): Promise<apiTypes.ResGetSettingsType> => {
  const response = await axios.get(API_ENDPOINTS.SETTING.GET_SETTINGS);
  return response.data;
};

export const getTableList = async (): Promise<apiTypes.ResgetTableListType> => {
  const response = await axios.get(API_ENDPOINTS.TABLE.GET_LIST);
  return response.data;
};

export const getFiles = async (
  path: string,
): Promise<apiTypes.ResGetFilesType> => {
  const response = await axios.post(API_ENDPOINTS.FILE.GET_LIST, {
    directoryPath: path,
  });
  return response.data;
};

export const importCsvByPath = async (
  requestBody: apiTypes.ReqImportCsvByPathType,
): Promise<apiTypes.ResImportCsvByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.IMPORT_CSV_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importExcelByPath = async (
  requestBody: apiTypes.ReqImportExcelByPathType,
): Promise<apiTypes.ResImportExcelByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.IMPORT_EXCEL_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importParquetByPath = async (
  requestBody: apiTypes.ReqImportParquetByPathType,
): Promise<apiTypes.ResImportParquetByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.IMPORT_PARQUET_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const getColumnList = async (
  tableName: string,
  isNumberOnly: string = "false",
): Promise<apiTypes.ResGetColumnInfoType> => {
  const response = await axios.post(API_ENDPOINTS.COLUMN.GET_LIST, {
    tableName: tableName,
    isNumberOnly: isNumberOnly,
  });
  return response.data;
};

export const fetchDataToJson = async (
  tableName: string,
  startRow: number = 1,
  fetchRows: number = 100,
): Promise<apiTypes.ResFetchDataToJsonType> => {
  const response = await axios.post(API_ENDPOINTS.TABLE.FETCH_DATA, {
    tableName: tableName,
    startRow: startRow,
    fetchRows: fetchRows,
  });
  return response.data;
};

export const createSimulationDataTable = async (
  requestBody: apiTypes.ReqCreateSimulationDataTableType,
): Promise<apiTypes.ResCreateSimulationDataTableType> => {
  const response = await axios.post(
    API_ENDPOINTS.TABLE.CREATE_SIMULATION_DATA,
    requestBody,
  );
  return response.data;
};

export const exportCsvByPath = async (
  requestBody: apiTypes.ReqExportCsvByPathType,
): Promise<apiTypes.ResExportCsvByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.EXPORT_CSV_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const exportExcelByPath = async (
  requestBody: apiTypes.ReqExportExcelByPathType,
): Promise<apiTypes.ResExportExcelByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.EXPORT_EXCEL_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const exportParquetByPath = async (
  requestBody: apiTypes.ReqExportParquetByPathType,
): Promise<apiTypes.ResExportParquetByPathType> => {
  const response = await axios.post(
    API_ENDPOINTS.DATA.EXPORT_PARQUET_BY_PATH,
    requestBody,
  );
  return response.data;
};

export const importCsv = async (
  file: File,
): Promise<apiTypes.ResImportCsvType> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(
    API_ENDPOINTS.DATA.IMPORT_CSV_BY_FILE,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );
  return response.data;
};

// 以下の関数は古いエンドポイントを使用しています
// 新しいAPIには対応するエンドポイントが存在しない可能性があります

export const outputCsv = async (
  tableName: string,
): Promise<apiTypes.ResOutputCsvType> => {
  const response = await axios.get("/output_csv", {
    params: {
      tableName: tableName,
    },
  });
  return response.data;
};

export const generateSimulationData = async (
  requestBody: apiTypes.ReqGenerateSimulationDataType,
): Promise<apiTypes.ResGenerateSimulationDataType> => {
  try {
    const response = await axios.post("/generate_simulation_data", requestBody);
    return response.data;
  } catch (error) {
    console.log(error);
    return { code: "NG", result: { tableName: "" }, message: "エラーです" };
  }
};

export const linearRegression = async (
  requestBody: apiTypes.ReqLinearRegressionType,
): Promise<apiTypes.ResLinearRegressionType> => {
  const response = await axios.post(
    API_ENDPOINTS.REGRESSION.LINEAR,
    requestBody,
  );
  return response.data;
};

export const calculateColumn = async (
  requestBody: apiTypes.ReqCalculateColumnType,
): Promise<apiTypes.ResCalculateColumnType> => {
  const response = await axios.post(
    API_ENDPOINTS.COLUMN.CALCULATE,
    requestBody,
  );
  return response.data;
};
