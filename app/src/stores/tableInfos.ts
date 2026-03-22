import { create } from "zustand";
import type { TableInfoType, TableInfosType } from "../types/commonTypes";
import { useTableChunkStore } from "./tableChunkStore";

export type TableInfosActions = {
  addTableInfo: (tableInfo: TableInfoType) => void;
  removeTableInfo: (tableName: string) => void;
  updateTableInfo: (tableName: string, tableInfo: TableInfoType) => void;
  activateTableInfo: (tableName: string) => void;
  /**
   * テーブルのメタ情報を部分更新する。
   * 列操作後のキャッシュ無効化と updateTableInfo を原子的に行う。
   */
  invalidateTable: (
    tableName: string,
    partial: Partial<Pick<TableInfoType, "columnList" | "totalRows">>,
  ) => void;
};

type TableInfosStore = {
  tableInfos: TableInfosType;
  activeTableName: string | null;
} & TableInfosActions;

export const useTableInfosStore = create<TableInfosStore>((set, get) => ({
  tableInfos: [],
  activeTableName: null,

  addTableInfo: (tableInfo) =>
    set(() => {
      const deactivatedInfos = get().tableInfos.map((info) => ({
        ...info,
        isActive: false,
      }));
      const newInfo = { ...tableInfo, isActive: true };
      return {
        tableInfos: [...deactivatedInfos, newInfo],
        activeTableName: tableInfo.tableName,
      };
    }),

  removeTableInfo: (tableName) =>
    set((state) => {
      const index = state.tableInfos.findIndex(
        (info) => info.tableName === tableName,
      );
      if (index === -1) return {};

      // フロント上のチャンクキャッシュも破棄する
      useTableChunkStore.getState().clearTable(tableName);

      const filtered = state.tableInfos.filter(
        (info) => info.tableName !== tableName,
      );
      const wasActive = state.tableInfos[index].isActive;

      if (!wasActive || filtered.length === 0) {
        return {
          tableInfos: filtered,
          activeTableName: wasActive ? null : state.activeTableName,
        };
      }

      // 削除したタブがアクティブだった場合、隣のタブをアクティブにする
      const nextIndex = Math.min(index, filtered.length - 1);
      const nextTable = filtered[nextIndex];
      return {
        tableInfos: filtered.map((info) => ({
          ...info,
          isActive: info.tableName === nextTable.tableName,
        })),
        activeTableName: nextTable.tableName,
      };
    }),

  updateTableInfo: (tableName, tableInfo) =>
    set((state) => ({
      tableInfos: state.tableInfos.map((info) =>
        info.tableName === tableName ? tableInfo : info,
      ),
    })),

  activateTableInfo: (tableName) =>
    set((state) => ({
      tableInfos: state.tableInfos.map((info) => ({
        ...info,
        isActive: info.tableName === tableName,
      })),
      activeTableName: tableName,
    })),

  invalidateTable: (tableName, partial) => {
    // バイナリキャッシュを無効化（列変更後に古いデータを捨てる）
    useTableChunkStore.getState().clearTable(tableName);

    set((state) => ({
      tableInfos: state.tableInfos.map((info) =>
        info.tableName === tableName ? { ...info, ...partial } : info,
      ),
    }));
  },
}));
