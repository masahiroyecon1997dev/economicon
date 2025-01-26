import axios from "../configs/axios";
import type * as apiTypes from '../types/apiTypes';


export async function importCsv(file: File): Promise<apiTypes.ResImportCsvType> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post('/import_csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { tableName: '' }, message: 'エラーです' };
  }
}

export async function outputCsv(tableName: string): Promise<apiTypes.ResOutputCsvType> {
  try {
    const response = await axios.get('/output_csv', {
      params: {
        tableName: tableName
      }
    });
    return response.data
  } catch (err) {
    console.log(err);
    return { code: -9999, result: { csvData: 'error' }, message: 'エラーです' };
  }
}


export async function fetchDataToJson(tableName: string, firstRow: number = 1, lastRow: number = 100): Promise<apiTypes.ResFetchDataToJsonType> {
  try {
    const response = await axios.get('/fetch_data_to_json', {
      params: {
        tableName: tableName,
        firstRow: firstRow,
        lastRow: lastRow
      }
    });
    return response.data
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { tableName: '', data: '' }, message: 'エラーです' };
  }
}

export async function getTableNameList(): Promise<apiTypes.ResGetTableNameListType> {
  try {
    const response = await axios.get('/get_table_name_list');
    return response.data
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { tableNameList: [] }, message: 'エラーです' };
  }
}

export async function getColumnNameList(tableName: string): Promise<apiTypes.ResGetColumnNameListType> {
  try {
    const response = await axios.get('/get_column_name_list', {
      params: {
        tableName: tableName
      }
    });
    return response.data
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { columnNameList: [] }, message: 'エラーです' };
  }
}

export async function generateSimulationData(requestBody: apiTypes.ReqGenerateSimulationDataType): Promise<apiTypes.ResGenerateSimulationDataType> {
  try {
    const response = await axios.post('/generate_simulation_data', requestBody);
    return response.data;
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { tableName: '' }, message: 'エラーです' };
  }
}

export async function linearRegression(requestBody: apiTypes.ReqLinearRegressionType): Promise<apiTypes.ResLinearRegressionType> {
  try {
    const response = await axios.post('/linear_regression', requestBody);
    return response.data;
  } catch (error) {
    console.log(error);
    return { code: -9999, result: { regressionResult: '' }, message: 'エラーです' };
  }
}
