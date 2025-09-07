import { ColumnType } from './commonTypes';

export type ResImportCsvType = { code: number; result: { tableName: string }; message: string };
export type ResOutputCsvType = { code: number; result: { csvData: string }; message: string };
export type ResFetchDataToJsonType = {
  code: number;
  result: { tableName: string; data: string };
  message: string;
};
export type ResGetTableNameListType = {
  code: string;
  result: { tableNameList: string[] };
  message: string;
};
export type ResGetColumnListType = {
  code: string;
  result: { columnList: ColumnType[] };
  message: string;
};
export type ResGenerateSimulationDataType = {
  code: string;
  result: { tableName: string };
  message: string;
};
export type ResLinearRegressionType = {
  code: string;
  result: { regressionResult: string };
  message: string;
};

export type ReqGenerateSimulationDataType = {
  tableName: string;
  numSamples: number;
  dataStructure: {
    columnName: string;
    dataType: string;
    value1: number;
    value2: number;
  }[];
};

export type ReqLinearRegressionType = {
  tableName: string;
  dependentVariable: string;
  explanatoryVariables: string[];
};
