import { create } from "zustand";
import type { TableInfoType, TableInfosType } from "../types/commonTypes";

export type TableInfosActions = {
  addTableInfo: (tableInfo: TableInfoType) => void;
  removeTableInfo: (tableName: string) => void;
  updateTableInfo: (tableName: string, tableInfo: TableInfoType) => void;
  activateTableInfo: (tableName: string) => void;
}

type TableInfosStore = {
  tableInfos: TableInfosType;
  activeTableName: string | null;
} & TableInfosActions;

export const useTableInfosStore = create<TableInfosStore>((set, get) => ({
  tableInfos: [],
  activeTableName: null,
  addTableInfo: (tableInfo) => set(() => {
    const deactivatedInfos = get().tableInfos.map(info => ({ ...info, isActive: false }));
    const newInfo = { ...tableInfo, isActive: true};
    return { tableInfos: [...deactivatedInfos, newInfo], activeTableName: tableInfo.tableName };
  }),

  removeTableInfo: (tableName) => set(state => {
    return { tableInfos: state.tableInfos.filter(info => info.tableName !== tableName) }
  }),

  updateTableInfo: (tableName, tableInfo) => set(state => {
    return { tableInfos: state.tableInfos.map(info => info.tableName === tableName ? tableInfo : info) }
  }),

  activateTableInfo: (tableName) => set(state => {
    return { tableInfos: state.tableInfos.map(info => ({...info, isActive: info.tableName === tableName })), activeTableName: tableName };
  }),
}));
