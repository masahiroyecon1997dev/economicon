import axios from "../configs/axios";
import type * as apiTypes from "../types/apiTypes";

export const getSettings = async (): Promise<apiTypes.ResGetSettingsType> => {
  const response = await axios.get("/get-settings");
  return response.data;
};

export const getTableNameList =
  async (): Promise<apiTypes.ResGetTableNameListType> => {
    const response = await axios.get("/get-table-list");
    return response.data;
  };

export const getFiles = async (
  path: string
): Promise<apiTypes.ResGetFilesType> => {
  const response = await axios.get("/get-files", {
    params: {
      directoryPath: path,
    },
  });
  return response.data;
};

export const importCsvByPath = async (
  requestBody: apiTypes.ReqImportCsvByPathType
): Promise<apiTypes.ResImportCsvByPathType> => {
  const response = await axios.post("/import-csv-by-path", requestBody);
  return response.data;
};

export const importExcelByPath = async (
  requestBody: apiTypes.ReqImportExcelByPathType
): Promise<apiTypes.ResImportExcelByPathType> => {
  const response = await axios.post("/import-excel-by-path", requestBody);
  return response.data;
};

export const importParquetByPath = async (
  requestBody: apiTypes.ReqImportParquetByPathType
): Promise<apiTypes.ResImportParquetByPathType> => {
  const response = await axios.post("/import-parquet-by-path", requestBody);
  return response.data;
};

export const getColumnList = async (
  tableName: string
): Promise<apiTypes.ResGetColumnInfoType> => {
  const response = await axios.get("/get-column-list", {
    params: {
      tableName: tableName,
    },
  });
  return response.data;
};

export const fetchDataToJson = async (
  tableName: string,
  startRow: number = 1,
  fetchRows: number = 100
): Promise<apiTypes.ResFetchDataToJsonType> => {
  const response = await axios.get("/fetch-data-to-json", {
    params: {
      tableName: tableName,
      startRow: startRow,
      fetchRows: fetchRows,
    },
  });
  return response.data;
};

export const createSimulationDataTable = async (
  requestBody: apiTypes.ReqCreateSimulationDataTableType
): Promise<apiTypes.ResCreateSimulationDataTableType> => {
  const response = await axios.post(
    "/create-simulation-data-table",
    requestBody
  );
  return response.data;
};

export const exportCsvByPath = async (
  requestBody: apiTypes.ReqExportCsvByPathType
): Promise<apiTypes.ResExportCsvByPathType> => {
  const response = await axios.post("/export-csv-by-path", requestBody);
  return response.data;
};

export const exportExcelByPath = async (
  requestBody: apiTypes.ReqExportExcelByPathType
): Promise<apiTypes.ResExportExcelByPathType> => {
  const response = await axios.post("/export-excel-by-path", requestBody);
  return response.data;
};

export const exportParquetByPath = async (
  requestBody: apiTypes.ReqExportParquetByPathType
): Promise<apiTypes.ResExportParquetByPathType> => {
  const response = await axios.post("/export-parquet-by-path", requestBody);
  return response.data;
};

export const importCsv = async (
  file: File
): Promise<apiTypes.ResImportCsvType> => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post("/import-csv-by-file", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const outputCsv = async (
  tableName: string
): Promise<apiTypes.ResOutputCsvType> => {
  const response = await axios.get("/output_csv", {
    params: {
      tableName: tableName,
    },
  });
  return response.data;
};

export const generateSimulationData = async (
  requestBody: apiTypes.ReqGenerateSimulationDataType
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
  requestBody: apiTypes.ReqLinearRegressionType
): Promise<apiTypes.ResLinearRegressionType> => {
  try {
    const response = await axios.post("/linear_regression", requestBody);
    return response.data;
  } catch (error) {
    console.log(error);
    return {
      code: "NG",
      result: { regressionResult: "" },
      message: "エラーです",
    };
  }
};
