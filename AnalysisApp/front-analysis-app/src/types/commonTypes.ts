export type TableDataType = { [key: string]: string | number | boolean | null }[] | null;
export type TableInfoType = { tableName: string, columnNameList: string[], isActive: boolean, data: TableDataType };
export type SelectListType = { value: string, name: string }[];

export type checkInputType = { isError: boolean, message: string };
