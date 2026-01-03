/**
 * API エンドポイント定義
 *
 * APIサーバーのエンドポイントURLを定義しています。
 * 各エンドポイントは対応するルーターとパスで構成されています。
 */

// 設定関連
export const API_SETTINGS_GET = "/setting/get";

// テーブル関連
export const API_TABLE_CREATE = "/table/create";
export const API_TABLE_CREATE_JOIN = "/table/create-join";
export const API_TABLE_CREATE_UNION = "/table/create-union";
export const API_TABLE_CREATE_SIMULATION_DATA = "/table/create-simulation-data";
export const API_TABLE_DELETE = "/table/delete";
export const API_TABLE_DUPLICATE = "/table/duplicate";
export const API_TABLE_RENAME = "/table/rename";
export const API_TABLE_LIST = "/table/list";
export const API_TABLE_CLEAR_ALL = "/table/clear-all";
export const API_TABLE_FETCH_DATA = "/table/fetch-data";

// カラム関連
export const API_COLUMN_ADD = "/column/add";
export const API_COLUMN_ADD_DUMMY = "/column/add-dummy";
export const API_COLUMN_DELETE = "/column/delete";
export const API_COLUMN_RENAME = "/column/rename";
export const API_COLUMN_ADD_LAG_LEAD = "/column/add-lag-lead";
export const API_COLUMN_ADD_SIMULATION = "/column/add-simulation";
export const API_COLUMN_CALCULATE = "/column/calculate";
export const API_COLUMN_DUPLICATE = "/column/duplicate";
export const API_COLUMN_TRANSFORM = "/column/transform";
export const API_COLUMN_LIST = "/column/list";
export const API_COLUMN_SORT = "/column/sort";

// データ入出力関連
export const API_DATA_IMPORT_CSV_BY_FILE = "/data/import-csv-by-file";
export const API_DATA_IMPORT_CSV_BY_PATH = "/data/import-csv-by-path";
export const API_DATA_IMPORT_TSV_BY_FILE = "/data/import-tsv-by-file";
export const API_DATA_IMPORT_EXCEL_BY_FILE = "/data/import-excel-by-file";
export const API_DATA_IMPORT_EXCEL_BY_PATH = "/data/import-excel-by-path";
export const API_DATA_IMPORT_PARQUET_BY_FILE = "/data/import-parquet-by-file";
export const API_DATA_IMPORT_PARQUET_BY_PATH = "/data/import-parquet-by-path";
export const API_DATA_EXPORT_CSV_BY_PATH = "/data/export-csv-by-path";
export const API_DATA_EXPORT_EXCEL_BY_PATH = "/data/export-excel-by-path";
export const API_DATA_EXPORT_PARQUET_BY_PATH = "/data/export-parquet-by-path";

// ファイル関連
export const API_FILE_LIST = "/file/list";

// 操作関連
export const API_OPERATION_INPUT_CELL_DATA = "/operation/input-cell-data";
export const API_OPERATION_FILTER_SINGLE_CONDITION =
  "/operation/filter-single-condition";

// 回帰分析関連
export const API_REGRESSION_LINEAR = "/regression/linear";
export const API_REGRESSION_LOGISTIC = "/regression/logistic";
export const API_REGRESSION_PROBIT = "/regression/probit";
export const API_REGRESSION_VARIABLE_EFFECTS = "/regression/variable-effects";
export const API_REGRESSION_FIXED_EFFECTS = "/regression/fixed-effects";

// 統計関連
export const API_STATISTICS_CONFIDENCE_INTERVAL =
  "/statistics/confidence-interval";
export const API_STATISTICS_DESCRIPTIVE = "/statistics/descriptive";
