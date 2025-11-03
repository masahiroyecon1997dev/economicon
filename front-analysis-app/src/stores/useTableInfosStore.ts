import { create } from "zustand";
import type { TableInfoType } from "../types/commonTypes";
import type { TableInfosType } from "../types/stateTypes";

export type TableInfosActions = {
  addTableInfo: (tableInfo: TableInfoType) => void;
  removeTableInfo: (tableName: string) => void;
  updateTableInfo: (tableName: string, tableInfo: TableInfoType) => void;
  activateTableInfo: (tableName: string) => void;
}

type TableInfosStore = TableInfosType & TableInfosActions;

const useTableInfosStore = create<TableInfosStore>((set) => ({
  tableInfos: [],
  addTableInfo: (tableInfo) => set((state) => ({
    tableInfos: [...state.tableInfos, tableInfo].map(info => info.tableName === tableInfo.tableName ? { ...info, isActive: true } : { ...info, isActive: false })
  })),
  removeTableInfo: (tableName) => set((state) => ({
    tableInfos: state.tableInfos.filter(info => info.tableName !== tableName)
  })),
  updateTableInfo: (tableName, tableInfo) => set((state) => ({
    tableInfos: state.tableInfos.map(info => info.tableName === tableName ? tableInfo : info)
  })),
  activateTableInfo: (tableName) => set((state) => ({
    tableInfos: state.tableInfos.map(info => info.tableName === tableName ? { ...info, isActive: true } : { ...info, isActive: false })
  })),
}));

export default useTableInfosStore;
