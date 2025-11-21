export type SettingsType = {
  osName: string;
  defaultFolderPath: string;
  displayRows: number;
  appLanguage: string;
  encoding: string;
  pathSeparator: string;
};

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
export type TableDataType = TalbeDataRowType[] | null;
export type ColumnType = { name: string; type: string };
export type TableInfoType = {
  tableName: string;
  columnList: ColumnType[];
  isActive: boolean;
  data: TableDataType;
  // numRow: number;
  // pageIndex: number;
};

export type TableListType = string[];
export type TableInfosType = TableInfoType[];

export type SortDirection = "asc" | "desc" | null;
export type SortField = "name" | "size" | "modifiedTime";

export type SelectListType = { value: string; name: string }[];

export type checkInputType = { isError: boolean; message: string };

export type DistributionType =
  | "uniform"
  | "exponential"
  | "normal"
  | "gamma"
  | "beta"
  | "weibull"
  | "lognormal"
  | "binomial"
  | "bernoulli"
  | "poisson"
  | "geometric"
  | "hypergeometric";

export type SimulationColumnSetting = {
  id: string;
  column_name: string;
  data_type: "distribution" | "fixed";
  distribution_type?: DistributionType;
  distribution_params?: Record<string, number>;
  fixed_value?: string | number;
};
