import axios from "../configs/axios";
import type * as apiTypes from "../types/apiTypes";

export const getSettings = async (
): Promise<apiTypes.ResGetSettingsType> => {
  const response = await axios.get("/get-settings");
  return response.data;
}

export const getFiles = async (path: string): Promise<apiTypes.ResGetFilesType> => {
  const response = await axios.get("/get-files", {
    params: {
      directoryPath: path,
    },
  });
  return response.data;
}

export const importCsvByPath = async (
  requestBody: apiTypes.ReqImportCsvByPathType
): Promise<apiTypes.ResImportCsvByPathType> => {
  const response = await axios.post("/import-csv-by-path", requestBody);
  return response.data;
}

export const importExcelByPath = async (
  requestBody: apiTypes.ReqImportExcelByPathType
): Promise<apiTypes.ResImportExcelByPathType> => {
  const response = await axios.post("/import-excel-by-path", requestBody);
  return response.data;
}

export const importParquetByPath = async (
  requestBody: apiTypes.ReqImportParquetByPathType
): Promise<apiTypes.ResImportParquetByPathType> => {
  const response = await axios.post("/import-parquet-by-path", requestBody);
  return response.data;
}

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
}

export const outputCsv = async (
  tableName: string
): Promise<apiTypes.ResOutputCsvType> => {
  try {
    const response = await axios.get("/output_csv", {
      params: {
        tableName: tableName,
      },
    });
    return response.data;
  } catch (err) {
    console.log(err);
    return { code: -9999, result: { csvData: "error" }, message: "エラーです" };
  }
}

export const fetchDataToJson = async (
  tableName: string,
  firstRow: number = 1,
  lastRow: number = 100
): Promise<apiTypes.ResFetchDataToJsonType> => {
  try {
    const response = await axios.get("/fetch-data-to-json", {
      params: {
        tableName: tableName,
        firstRow: firstRow,
        lastRow: lastRow,
      },
    });
    return response.data;
  } catch (error) {
    console.log(error);
    return {
      code: -9999,
      result: { tableName: "", data: "" },
      message: "エラーです",
    };
  }
}

export const getTableNameList = async (): Promise<apiTypes.ResGetTableNameListType> => {
  try {
    const response = await axios.get("/get-table-name-list");
    return response.data;
  } catch (error) {
    console.log(error);
    return { code: "NG", result: { tableNameList: [] }, message: "エラーです" };
  }
}

export const getColumnInfoList = async (
  tableName: string
): Promise<apiTypes.ResGetColumnInfoType> => {
  try {
    const response = await axios.get("/get-column-info-list", {
      params: {
        tableName: tableName,
      },
    });
    return response.data;
  } catch (error) {
    console.log(error);
    return { code: "NG", result: { tableName: "", columnInfoList: [] }, message: "エラーです" };
  }
}

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
}

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
}
