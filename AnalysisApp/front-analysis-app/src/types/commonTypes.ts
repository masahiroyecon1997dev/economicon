export type TableDataCellType = string | number | boolean | null;
export type TalbeDataRowType = { [key: string]: TableDataCellType };
export type TableDataType = TalbeDataRowType[] | null;
export type ColumnType = { id: string; name: string };
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
