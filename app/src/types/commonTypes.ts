import type { DistributionParamsType as ApiDistributionType } from "@/api/model";

export type FileType = {
  name: string;
  isFile: boolean;
  size: number;
  modifiedTime: string;
};

export type FilesType = {
  files: FileType[];
  directoryPath: string;
};

export type TableDataCellType = string | number | boolean | null;
export type TalbeDataRowType = { [key: string]: TableDataCellType };
export type ColumnType = { name: string; type: string };

/** テーブルメタ情報（行データはtableChunkStoreで管理） */
export type TableInfoType = {
  tableName: string;
  columnList: ColumnType[];
  totalRows: number;
  isActive: boolean;
};

export type TableListType = string[];
export type TableInfosType = TableInfoType[];

export type SortDirection = "asc" | "desc" | null;
export type SortField = "name" | "size" | "modifiedTime";

export type SelectListType = { value: string; name: string }[];

export type checkInputType = { isError: boolean; message: string };

export type DistributionType = ApiDistributionType;

export type SimulationColumnSetting = {
  id: string;
  columnName: string;
  dataType: "distribution" | "fixed";
  distributionType?: DistributionType;
  distributionParams?: Record<string, number>;
  fixedValue: string | number;
  errorMessage: {
    columnName: string | undefined;
    distributionParams: Record<string, string | undefined> | undefined;
    fixedValue: string | undefined;
  };
};

export type DropmenuPositionType =
  | "top"
  | "bottom"
  | "bottom-left"
  | "bottom-right"
  | "top-left"
  | "top-right";

export type LinearRegressionResultType = {
  resultId: string;
  tableName: string;
  dependentVariable: string;
  explanatoryVariables: string[];
  regressionResult: string;
  parameters: Array<{
    variable: string;
    coefficient: number;
    standardError: number | null;
    pValue: number | null;
    tValue: number | null;
    confidenceIntervalLower: number | null;
    confidenceIntervalUpper: number | null;
  }>;
  modelStatistics: {
    nObservations: number;
    R2?: number;
    adjustedR2?: number;
    fValue?: number;
    fProbability?: number;
    AIC?: number;
    BIC?: number;
    logLikelihood?: number;
    pseudoRSquared?: number;
  };
};

export type TauriFile = File & { path: string };
