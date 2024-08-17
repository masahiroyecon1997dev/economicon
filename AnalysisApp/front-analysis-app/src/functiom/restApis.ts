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
    return {code: -9999, tableName: ''}
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
    return {code: -9999, csvData: 'error'}
  }
}


export async function fetchDataToJson(tableName: string): Promise<apiTypes.ResFetchDataToJsonType> {
  try {
    const response = await axios.get('/fetch_data_to_json', {
      params: {
        tableName: tableName
      }
    });
    return response.data
  } catch (error) {
    console.log(error);
    return {code: -9999, tableName: '', data: ''}
  }
}

export async function getTableNameList(): Promise<apiTypes.ResGetTableNameListType> {
  try {
    const response = await axios.get('/get_table_name_list');
    return response.data
  } catch (error) {
    console.log(error);
    return {code: -9999, tableNameList: []}
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
    return {code: -9999, columnNameList: []}
  }
}
