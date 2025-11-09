export type SettingsType = {
  defaultFolderPath: string;
  displayRows: number;
  appLanguage: string;
  encoding: string;
  pathSeparator: string;
}

export type FileType = {
  name: string;
  isFile: boolean;
  size: number;
  modifiedTime: string;
}

export type FilesType = {
  files: FileType[],
  directoryPath: string;
}

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


export type SelectListType = { value: string; name: string }[];

export type checkInputType = { isError: boolean; message: string };
