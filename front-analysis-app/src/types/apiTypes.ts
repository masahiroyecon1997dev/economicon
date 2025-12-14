import type { ColumnType, FilesType, SettingsType } from "./commonTypes";

export type BaseResponseType = {
  code: string;
  message: string;
};

export type ResGetSettingsType = BaseResponseType & {
  result: SettingsType;
};

export type ResGetFilesType = BaseResponseType & {
  result: FilesType;
};

export type ReqImportCsvByPathType = {
  filePath: string;
  tableName: string;
  separator: string;
};

export type ResImportCsvByPathType = BaseResponseType & {
  result: { tableName: string };
};

export type ReqImportExcelByPathType = {
  filePath: string;
  tableName: string;
  sheetName: string;
};

export type ResImportExcelByPathType = BaseResponseType & {
  result: { tableName: string };
};

export type ReqImportParquetByPathType = {
  filePath: string;
  tableName: string;
};

export type ResImportParquetByPathType = BaseResponseType & {
  result: { tableName: string };
};

export type ResGetColumnInfoType = BaseResponseType & {
  result: { tableName: string; columnInfoList: ColumnType[] };
};

export type ResFetchDataToJsonType = BaseResponseType & {
  result: { tableName: string; data: string };
};

export type ReqCreateSimulationDataTableType = {
  tableName: string;
  tableNumberOfRows: number;
  columnSettings: Array<{
    columnName: string;
    dataType: "fixed" | "distribution";
    fixedValue?: string | number;
    distributionType?: string;
    distributionParams?: Record<string, number>;
  }>;
};

export type ResCreateSimulationDataTableType = BaseResponseType & {
  result: { tableName: string };
};

export type ResImportCsvType = BaseResponseType & {
  result: { tableName: string };
};

export type ResOutputCsvType = BaseResponseType & {
  result: { csvData: string };
};

export type ResGetTableNameListType = BaseResponseType & {
  result: { tableNameList: string[] };
};

export type ReqExportCsvByPathType = {
  tableName: string;
  directoryPath: string;
  fileName: string;
  separator?: string;
};

export type ResExportCsvByPathType = BaseResponseType & {
  result: { filePath: string };
};

export type ReqExportExcelByPathType = {
  tableName: string;
  directoryPath: string;
  fileName: string;
  sheetName?: string;
};

export type ResExportExcelByPathType = BaseResponseType & {
  result: { filePath: string };
};

export type ReqExportParquetByPathType = {
  tableName: string;
  directoryPath: string;
  fileName: string;
};

export type ResExportParquetByPathType = BaseResponseType & {
  result: { filePath: string };
};

export type ResGenerateSimulationDataType = BaseResponseType & {
  result: { tableName: string };
};

export type ResLinearRegressionType = BaseResponseType & {
  result: { regressionResult: string };
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
