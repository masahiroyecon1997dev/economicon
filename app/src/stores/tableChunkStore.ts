/**
 * テーブルチャンクキャッシュストア
 *
 * Apache Arrow IPC の生バイナリをチャンク単位でキャッシュする。
 * - バイナリはミュータブルな Map で保持し、パフォーマンスを最大化
 * - versions カウンタだけが Zustand の反応的状態（再レンダートリガー）
 * - MAX_CACHE_CHUNKS を超えると挿入順 LRU で古いチャンクを削除
 */
import { create } from "zustand";

export const CHUNK_SIZE = 500;
const MAX_CACHE_CHUNKS = 20;

type TableChunkStore = {
  /**
   * チャンクバイナリキャッシュ（直接購読しないこと）
   *   key: tableName → chunkIndex → Uint8Array (Arrow IPC bytes)
   */
  _cache: Map<string, Map<number, Uint8Array>>;

  /**
   * テーブルごとのバージョンカウンタ。
   * チャンク追加 / テーブル無効化時にインクリメントし、
   * コンポーネントの再レンダーをトリガーする。
   */
  versions: Record<string, number>;

  /** チャンクデータを保存する */
  setChunk: (tableName: string, chunkIndex: number, data: Uint8Array) => void;

  /** チャンクデータを取得する（未キャッシュなら undefined） */
  getChunk: (tableName: string, chunkIndex: number) => Uint8Array | undefined;

  /** チャンクがキャッシュ済みかどうか */
  hasChunk: (tableName: string, chunkIndex: number) => boolean;

  /** テーブルのキャッシュを全て無効化する（列操作後に呼ぶ） */
  clearTable: (tableName: string) => void;

  /** 全テーブルのキャッシュを無効化する */
  clearAll: () => void;
};

export const useTableChunkStore = create<TableChunkStore>((set, get) => ({
  _cache: new Map(),
  versions: {},

  setChunk: (tableName, chunkIndex, data) => {
    const state = get();
    let tableCache = state._cache.get(tableName);
    if (!tableCache) {
      tableCache = new Map();
      state._cache.set(tableName, tableCache);
    }

    // LRU: 上限を超えたら最古エントリを削除（Map は挿入順）
    if (tableCache.size >= MAX_CACHE_CHUNKS && !tableCache.has(chunkIndex)) {
      const oldest = tableCache.keys().next().value;
      if (oldest !== undefined) tableCache.delete(oldest);
    }

    tableCache.set(chunkIndex, data);

    // バージョンカウンタのみ Zustand で更新（再レンダートリガー）
    set((s) => ({
      versions: {
        ...s.versions,
        [tableName]: (s.versions[tableName] ?? 0) + 1,
      },
    }));
  },

  getChunk: (tableName, chunkIndex) =>
    get()._cache.get(tableName)?.get(chunkIndex),

  hasChunk: (tableName, chunkIndex) =>
    get()._cache.get(tableName)?.has(chunkIndex) ?? false,

  clearTable: (tableName) => {
    get()._cache.delete(tableName);
    set((s) => ({
      versions: {
        ...s.versions,
        [tableName]: (s.versions[tableName] ?? 0) + 1,
      },
    }));
  },

  clearAll: () => {
    get()._cache.clear();
    set({ versions: {} });
  },
}));
