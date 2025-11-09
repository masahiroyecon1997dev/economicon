import type { TableInfoType } from "./commonTypes";

export type TableListType = { tableList: string[] };
export type TableInfosType = { tableInfos: TableInfoType[] };

export type SortDirection = 'asc' | 'desc' | null;
export type SortField = 'name' | 'size' | 'modifiedTime';
