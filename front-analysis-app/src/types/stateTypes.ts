import type { TableInfoType } from "./commonTypes";

export type TableListType = string[];
export type TableInfosType = TableInfoType[];

export type SortDirection = 'asc' | 'desc' | null;
export type SortField = 'name' | 'size' | 'modifiedTime';
