/**
 * 仮想スクロール用のテーブルデータ管理フック
 * チャンク単位でデータを取得・キャッシュする
 */
import { tableFromIPC, type Table } from "apache-arrow";
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchDataToArrow } from "../functions/restApis";
import type { TalbeDataRowType } from "../types/commonTypes";

const CHUNK_SIZE = 500;
const MAX_CACHE_CHUNKS = 20; // キャッシュサイズを少し増やす

/**
 * Arrow Tableを行オブジェクトの配列に変換
 *
 * @param table Apache Arrowテーブル
 * @returns 行データの配列
 */
function arrowTableToRows(table: Table): TalbeDataRowType[] {
  const rows: TalbeDataRowType[] = [];
  const numRows = table.numRows;
  const schema = table.schema;

  for (let i = 0; i < numRows; i++) {
    const row: TalbeDataRowType = {};
    for (const field of schema.fields) {
      const column = table.getChild(field.name);
      row[field.name] = column?.get(i);
    }
    rows.push(row);
  }

  return rows;
}

interface ChunkData {
  startRow: number;
  endRow: number;
  data: TalbeDataRowType[];
  timestamp: number;
}

interface UseVirtualTableDataOptions {
  tableName: string;
  totalRows: number;
  enabled?: boolean;
}

export function useVirtualTableData({
  tableName,
  enabled = true,
}: UseVirtualTableDataOptions) {
  // チャンクキャッシュ（チャンクインデックス → データ）
  const [chunks, setChunks] = useState<Map<number, ChunkData>>(new Map());
  // ロード中のチャンクインデックスのセット
  const [loadingChunks, setLoadingChunks] = useState<Set<number>>(new Set());
  // エラー状態
  const [error, setError] = useState<Error | null>(null);

  // 現在フェッチ中のリクエストを追跡（重複リクエスト防止）
  const fetchingChunksRef = useRef<Set<number>>(new Set());

  /**
   * 行インデックスからチャンクインデックスを計算
   */
  const getChunkIndex = useCallback((rowIndex: number): number => {
    return Math.floor(rowIndex / CHUNK_SIZE);
  }, []);

  /**
   * チャンクインデックスから開始行を計算（1-based）
   */
  const getChunkStartRow = useCallback((chunkIndex: number): number => {
    return chunkIndex * CHUNK_SIZE + 1;
  }, []);

  /**
   * LRUキャッシュのクリーンアップ
   */
  const cleanupCache = useCallback(() => {
    setChunks((prevChunks) => {
      if (prevChunks.size <= MAX_CACHE_CHUNKS) {
        return prevChunks;
      }

      // タイムスタンプでソートして古いものから削除
      const sortedChunks = Array.from(prevChunks.entries()).sort(
        ([, a], [, b]) => a.timestamp - b.timestamp,
      );

      const newChunks = new Map<number, ChunkData>();
      const keepCount = Math.floor(MAX_CACHE_CHUNKS * 0.8); // 80%を保持

      for (
        let i = sortedChunks.length - keepCount;
        i < sortedChunks.length;
        i++
      ) {
        const [index, data] = sortedChunks[i];
        newChunks.set(index, data);
      }

      return newChunks;
    });
  }, []);

  /**
   * チャンクをフェッチ
   */
  const fetchChunk = useCallback(
    async (chunkIndex: number) => {
      if (!enabled) return;

      // すでにキャッシュされている場合はスキップ
      if (chunks.has(chunkIndex)) {
        return;
      }

      // すでにフェッチ中の場合はスキップ
      if (fetchingChunksRef.current.has(chunkIndex)) {
        return;
      }

      try {
        fetchingChunksRef.current.add(chunkIndex);
        setLoadingChunks((prev) => new Set(prev).add(chunkIndex));

        const startRow = getChunkStartRow(chunkIndex);

        // データをフェッチ
        const arrowBytes = await fetchDataToArrow(
          tableName,
          startRow,
          CHUNK_SIZE,
        );

        // Arrow IPCからテーブルを復元
        const table = tableFromIPC(arrowBytes);

        // Arrow TableをJavaScriptオブジェクトの配列に変換
        const rows = arrowTableToRows(table);

        // 実際の終了行を計算
        const endRow = startRow + table.numRows - 1;

        // キャッシュに追加
        setChunks((prevChunks) => {
          const newChunks = new Map(prevChunks);
          newChunks.set(chunkIndex, {
            startRow,
            endRow,
            data: rows,
            timestamp: Date.now(),
          });
          return newChunks;
        });

        setError(null);
        cleanupCache();
      } catch (err) {
        console.error(`Failed to fetch chunk ${chunkIndex}:`, err);
        setError(err instanceof Error ? err : new Error("Unknown error"));
      } finally {
        fetchingChunksRef.current.delete(chunkIndex);
        setLoadingChunks((prev) => {
          const newSet = new Set(prev);
          newSet.delete(chunkIndex);
          return newSet;
        });
      }
    },
    [tableName, enabled, chunks, getChunkStartRow, cleanupCache],
  );

  /**
   * 行インデックスから行データを取得
   */
  const getRowData = useCallback(
    (rowIndex: number): TalbeDataRowType | undefined => {
      const chunkIndex = getChunkIndex(rowIndex);
      const chunk = chunks.get(chunkIndex);

      if (!chunk) {
        return undefined;
      }

      // チャンク内でのインデックスを計算（0-based）
      const indexInChunk = rowIndex - (chunk.startRow - 1);

      return chunk.data[indexInChunk];
    },
    [chunks, getChunkIndex],
  );

  /**
   * 指定範囲の行データを取得（チャンクをプリフェッチ）
   */
  const prefetchRange = useCallback(
    (startIndex: number, endIndex: number) => {
      if (!enabled) return;

      const startChunk = getChunkIndex(startIndex);
      const endChunk = getChunkIndex(endIndex);

      // 必要なチャンクをすべてフェッチ
      for (let i = startChunk; i <= endChunk; i++) {
        fetchChunk(i);
      }
    },
    [enabled, getChunkIndex, fetchChunk],
  );

  /**
   * キャッシュをクリア
   */
  const clearCache = useCallback(() => {
    setChunks(new Map());
    setLoadingChunks(new Set());
    setError(null);
    fetchingChunksRef.current.clear();
  }, []);

  // テーブル名が変更されたらキャッシュをクリア
  useEffect(() => {
    clearCache();
  }, [tableName, clearCache]);

  return {
    getRowData,
    prefetchRange,
    fetchChunk,
    clearCache,
    isLoading: loadingChunks.size > 0,
    loadingChunks: Array.from(loadingChunks),
    error,
    cachedChunks: Array.from(chunks.keys()),
  };
}
