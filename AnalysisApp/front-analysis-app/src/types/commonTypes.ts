export type TableDataType = { [key: string]: string | number | boolean | null }[] | null;
export type TableInfoType = { tableName: string, columnNameList: string[], data: TableDataType }
