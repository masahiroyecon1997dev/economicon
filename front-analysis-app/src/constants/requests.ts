/**
 * API エンドポイント定義
 *
 * APIサーバーのエンドポイントURLを定義しています。
 * 各エンドポイントは対応するルーターとパスで構成されています。
 */

export const API_ENDPOINTS = {
  SETTING: {
    GET_SETTINGS: "/setting/get-settings",
  },
  TABLE: {
    CREATE: "/table/create",
    CREATE_JOIN: "/table/create-join",
    CREATE_UNION: "/table/create-union",
    CREATE_SIMULATION_DATA: "/table/create-simulation-data",
    DELETE: "/table/delete",
    DUPLICATE: "/table/duplicate",
    RENAME: "/table/rename",
    GET_LIST: "/table/get-list",
    CLEAR_ALL: "/table/clear-all",
    FETCH_DATA: "/table/fetch-data",
  },
  COLUMN: {
    ADD: "/column/add",
    ADD_DUMMY: "/column/add-dummy",
    DELETE: "/column/delete",
    RENAME: "/column/rename",
    ADD_LAG_LEAD: "/column/add-lag-lead",
    ADD_SIMULATION: "/column/add-simulation",
    CALCULATE: "/column/calculate",
    DUPLICATE: "/column/duplicate",
    TRANSFORM: "/column/transform",
    GET_LIST: "/column/get-list",
    SORT: "/column/sort",
  },
  DATA: {
    IMPORT_CSV_BY_FILE: "/data/import-csv-by-file",
    IMPORT_CSV_BY_PATH: "/data/import-csv-by-path",
    IMPORT_TSV_BY_FILE: "/data/import-tsv-by-file",
    IMPORT_EXCEL_BY_FILE: "/data/import-excel-by-file",
    IMPORT_EXCEL_BY_PATH: "/data/import-excel-by-path",
    IMPORT_PARQUET_BY_FILE: "/data/import-parquet-by-file",
    IMPORT_PARQUET_BY_PATH: "/data/import-parquet-by-path",
    EXPORT_CSV_BY_PATH: "/data/export-csv-by-path",
    EXPORT_EXCEL_BY_PATH: "/data/export-excel-by-path",
    EXPORT_PARQUET_BY_PATH: "/data/export-parquet-by-path",
  },
  FILE: {
    GET_LIST: "/file/get-list",
  },
  OPERATION: {
    INPUT_CELL_DATA: "/operation/input-cell-data",
    FILTER_SINGLE_CONDITION: "/operation/filter-single-condition",
  },
  REGRESSION: {
    LINEAR: "/regression/linear",
    LOGISTIC: "/regression/logistic",
    PROBIT: "/regression/probit",
    VARIABLE_EFFECTS: "/regression/variable-effects",
    FIXED_EFFECTS: "/regression/fixed-effects",
  },
  STATISTICS: {
    CONFIDENCE_INTERVAL: "/statistics/confidence-interval",
    DESCRIPTIVE: "/statistics/descriptive",
  },
} as const;

// 後方互換性のための定数エクスポート（非推奨）
export const API_SETTINGS_GET = API_ENDPOINTS.SETTING.GET_SETTINGS;
export const API_TABLE_CREATE = API_ENDPOINTS.TABLE.CREATE;
export const API_TABLE_CREATE_JOIN = API_ENDPOINTS.TABLE.CREATE_JOIN;
export const API_TABLE_CREATE_UNION = API_ENDPOINTS.TABLE.CREATE_UNION;
export const API_TABLE_CREATE_SIMULATION_DATA =
  API_ENDPOINTS.TABLE.CREATE_SIMULATION_DATA;
export const API_TABLE_DELETE = API_ENDPOINTS.TABLE.DELETE;
export const API_TABLE_DUPLICATE = API_ENDPOINTS.TABLE.DUPLICATE;
export const API_TABLE_RENAME = API_ENDPOINTS.TABLE.RENAME;
export const API_TABLE_LIST = API_ENDPOINTS.TABLE.GET_LIST;
export const API_TABLE_CLEAR_ALL = API_ENDPOINTS.TABLE.CLEAR_ALL;
export const API_TABLE_FETCH_DATA = API_ENDPOINTS.TABLE.FETCH_DATA;
export const API_COLUMN_ADD = API_ENDPOINTS.COLUMN.ADD;
export const API_COLUMN_ADD_DUMMY = API_ENDPOINTS.COLUMN.ADD_DUMMY;
export const API_COLUMN_DELETE = API_ENDPOINTS.COLUMN.DELETE;
export const API_COLUMN_RENAME = API_ENDPOINTS.COLUMN.RENAME;
export const API_COLUMN_ADD_LAG_LEAD = API_ENDPOINTS.COLUMN.ADD_LAG_LEAD;
export const API_COLUMN_ADD_SIMULATION = API_ENDPOINTS.COLUMN.ADD_SIMULATION;
export const API_COLUMN_CALCULATE = API_ENDPOINTS.COLUMN.CALCULATE;
export const API_COLUMN_DUPLICATE = API_ENDPOINTS.COLUMN.DUPLICATE;
export const API_COLUMN_TRANSFORM = API_ENDPOINTS.COLUMN.TRANSFORM;
export const API_COLUMN_LIST = API_ENDPOINTS.COLUMN.GET_LIST;
export const API_COLUMN_SORT = API_ENDPOINTS.COLUMN.SORT;
export const API_DATA_IMPORT_CSV_BY_FILE =
  API_ENDPOINTS.DATA.IMPORT_CSV_BY_FILE;
export const API_DATA_IMPORT_CSV_BY_PATH =
  API_ENDPOINTS.DATA.IMPORT_CSV_BY_PATH;
export const API_DATA_IMPORT_TSV_BY_FILE =
  API_ENDPOINTS.DATA.IMPORT_TSV_BY_FILE;
export const API_DATA_IMPORT_EXCEL_BY_FILE =
  API_ENDPOINTS.DATA.IMPORT_EXCEL_BY_FILE;
export const API_DATA_IMPORT_EXCEL_BY_PATH =
  API_ENDPOINTS.DATA.IMPORT_EXCEL_BY_PATH;
export const API_DATA_IMPORT_PARQUET_BY_FILE =
  API_ENDPOINTS.DATA.IMPORT_PARQUET_BY_FILE;
export const API_DATA_IMPORT_PARQUET_BY_PATH =
  API_ENDPOINTS.DATA.IMPORT_PARQUET_BY_PATH;
export const API_DATA_EXPORT_CSV_BY_PATH =
  API_ENDPOINTS.DATA.EXPORT_CSV_BY_PATH;
export const API_DATA_EXPORT_EXCEL_BY_PATH =
  API_ENDPOINTS.DATA.EXPORT_EXCEL_BY_PATH;
export const API_DATA_EXPORT_PARQUET_BY_PATH =
  API_ENDPOINTS.DATA.EXPORT_PARQUET_BY_PATH;
export const API_FILE_LIST = API_ENDPOINTS.FILE.GET_LIST;
export const API_OPERATION_INPUT_CELL_DATA =
  API_ENDPOINTS.OPERATION.INPUT_CELL_DATA;
export const API_OPERATION_FILTER_SINGLE_CONDITION =
  API_ENDPOINTS.OPERATION.FILTER_SINGLE_CONDITION;
export const API_REGRESSION_LINEAR = API_ENDPOINTS.REGRESSION.LINEAR;
export const API_REGRESSION_LOGISTIC = API_ENDPOINTS.REGRESSION.LOGISTIC;
export const API_REGRESSION_PROBIT = API_ENDPOINTS.REGRESSION.PROBIT;
export const API_REGRESSION_VARIABLE_EFFECTS =
  API_ENDPOINTS.REGRESSION.VARIABLE_EFFECTS;
export const API_REGRESSION_FIXED_EFFECTS =
  API_ENDPOINTS.REGRESSION.FIXED_EFFECTS;
export const API_STATISTICS_CONFIDENCE_INTERVAL =
  API_ENDPOINTS.STATISTICS.CONFIDENCE_INTERVAL;
export const API_STATISTICS_DESCRIPTIVE = API_ENDPOINTS.STATISTICS.DESCRIPTIVE;
