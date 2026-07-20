import type { DistributionType as ApiDistributionType } from "@/api/model";

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
export type TableDataRowType = { [key: string]: TableDataCellType };
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
  /** モデル種別（ols / wls / logit / probit 等）。AnalysisResultDetail.modelType に対応 */
  modelType?: string | null;
  parameters: Array<{
    variable: string;
    coefficient: number;
    standardError: number | null;
    pValue: number | null;
    tValue: number | null;
    confidenceIntervalLower: number | null;
    confidenceIntervalUpper: number | null;
  }>;
  marginalEffects?: Array<{
    variable: string;
    marginalEffect: number;
    standardError: number | null;
    tValue: number | null;
    pValue: number | null;
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
    logLikelihoodNull?: number;
    lrStatistic?: number;
    lrDf?: number;
    lrPValue?: number;
    /** パネル固定効果・変量効果モデル固有 */
    nEntities?: number;
    R2Within?: number;
    R2Between?: number;
    R2Overall?: number;
    fPooled?: {
      statistic: number;
      pValue: number;
    };
  };
  diagnostics?: {
    censoringLimits?: { left: number | null; right: number | null } | null;
    sigma?: number | null;
    waldTest?: {
      statistic: number;
      pValue: number;
      df: number;
      description: string;
    } | null;
    lrTest?: {
      statistic: number;
      pValue: number;
      df: number;
      description: string;
    } | null;
  } | null;
};

export type TauriFile = File & { path: string };

// GET /api/analysis/results/{id} の resultData に格納される信頼区間の計算結果
export type ConfidenceIntervalResultData = {
  resultId: string;
  tableName: string;
  columnName: string;
  statistic: { type: string; value: number | null };
  confidenceInterval: { lower: number; upper: number };
  confidenceLevel: number;
};
