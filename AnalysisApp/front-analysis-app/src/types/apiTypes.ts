export type ResImportCsvType = { code: number, result: { tableName: string }, message: string };
export type ResOutputCsvType = { code: number, result: { csvData: string }, message: string };
export type ResFetchDataToJsonType = { code: number, result: { tableName: string, data: string }, message: string };
export type ResGetTableNameListType = { code: number, result: { tableNameList: string[] }, message: string };
export type ResGetColumnNameListType = { code: number, result: { columnNameList: string[] }, message: string };
export type ResGenerateSimulationDataType = { code: number, result: { tableName: string }, message: string };



export type ReqGenerateSimulationDataType = {
  tableName: string,
  numSamples: number,
  dataStructure: {
    columnName: string,
    coefficient: number,
    minValue: number,
    maxValue: number
  }[];
  errorMean: number,
  errorVariance: number
};
