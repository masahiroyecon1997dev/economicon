import { create } from "zustand";
import type { TableListType } from "../types/stateTypes";

export type TableListActions = {
  setTableList: (tableList: string[]) => void;
  addTableName: (tableName: string) => void;
  removeTableName: (tableName: string) => void;
}

type TableListStore = TableListType & TableListActions;

export const useTableListStore = create<TableListStore>((set) => ({
  tableList: [],
  setTableList: (tableList) => set(() => ({ tableList })),
  addTableName: (tableName) => set((state) => ({
    tableList: [...state.tableList, tableName]
  })),
  removeTableName: (tableName) => set((state) => ({
    tableList: state.tableList.filter(name => name !== tableName)
  }))
}));
