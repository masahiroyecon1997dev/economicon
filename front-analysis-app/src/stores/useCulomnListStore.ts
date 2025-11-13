import { create } from "zustand";
import type { ColumnType } from "../types/commonTypes";

export type ColumnListActions = {
  setColumnList: (columnList: ColumnType[]) => void;
}

type ColumnListStore = { columnList: ColumnType[] } & ColumnListActions;

export const useColumnListStore = create<ColumnListStore>((set) => ({
  columnList: [],
  setColumnList: (columnList) => set({ columnList }),
}));
