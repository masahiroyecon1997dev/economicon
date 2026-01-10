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
};
