import { create } from "zustand";
import type { TableInfoType } from "../types/commonTypes";
import type { TableInfosType } from "../types/stateTypes";

export type TableInfosActions = {
  addTableInfo: (tableInfo: TableInfoType) => void;
  removeTableInfo: (tableName: string) => void;
  updateTableInfo: (tableName: string, tableInfo: TableInfoType) => void;
  activateTableInfo: (tableName: string) => void;
}

type TableInfosStore = {
    tableInfos: TableInfosType;
} & TableInfosActions;

export const useTableInfosStore = create<TableInfosStore>((set, get) => ({
  tableInfos: [],
  addTableInfo: (tableInfo) => set(() => {
    const deactivatedInfos = get().tableInfos.map(info => ({ ...info, isActive: false }));
    const newInfo = { ...tableInfo, isActive: true};
    return { tableInfos: [...deactivatedInfos, newInfo] };
  }),

  removeTableInfo: (tableName) => set(state => {
    return { tableInfos: state.tableInfos.filter(info => info.tableName !== tableName) }
  }),

  updateTableInfo: (tableName, tableInfo) => set(state => {
    return { tableInfos: state.tableInfos.map(info => info.tableName === tableName ? tableInfo : info) }
  }),

  activateTableInfo: (tableName) => set(state => {
    return { tableInfos: state.tableInfos.map(info => ({...info, isActive: info.tableName === tableName })) }
  }),
}));
