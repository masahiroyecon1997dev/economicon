import type { ColumnType, FilesType, SettingsType } from "./commonTypes";

export type ResGetSettingsType = {
  code: string;
  result: SettingsType;
  message: string;
}

export type ResGetFilesType = {
  code: string;
  result: FilesType;
  message: string;
};

export type ReqImportCsvByPathType = {
  filePath: string;
  tableName: string;
  separator: string;
};

export type ResImportCsvByPathType = {
  code: string;
  result: { tableName: string };
  message: string;
};

export type ReqImportExcelByPathType = {
  filePath: string;
  tableName: string;
  sheetName: string;
};

export type ResImportExcelByPathType = {
  code: string;
  result: { tableName: string };
  message: string;
};

export type ReqImportParquetByPathType = {
  filePath: string;
  tableName: string;
};

export type ResImportParquetByPathType = {
  code: string;
  result: { tableName: string };
  message: string;
};

export type ResGetColumnInfoType = {
  code: string;
  result: { tableName: string; columnInfoList: ColumnType[] };
  message: string;
};

export type ResFetchDataToJsonType = {
  code: string;
  result: { tableName: string; data: string };
  message: string;
};

export type ResImportCsvType = {
  code: number;
  result: { tableName: string };
  message: string;
};
export type ResOutputCsvType = {
  code: number;
  result: { csvData: string };
  message: string;
};

export type ResGetTableNameListType = {
  code: string;
  result: { tableNameList: string[] };
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
