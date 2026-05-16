/**
 * 仮想スクロール用テーブルデータ管理フック（刷新版）
 *
 * バイナリキャッシュは Zustand の tableChunkStore で管理し、
 * パース済み行は useRef の parsedChunksRef でローカルキャッシュする。
 *
 * フロー:
 *   1. マウント時に chunk 0 を無条件フェッチ
 *   2. Arrow スキーマメタデータから totalRows を取得し tableInfosStore を更新
 *   3. 仮想スクロール中は prefetchRange で先読みチャンクを取得
 */
import { fetchDataToArrow } from "@/api/bridge/tauri-commands";
import { CHUNK_SIZE, useTableChunkStore } from "@/stores/tableChunkStore";
import { useTableInfosStore } from "@/stores/tableInfos";
import type { TalbeDataRowType } from "@/types/commonTypes";
import { tableFromIPC, type Table as ArrowTable } from "apache-arrow";
import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Arrow  行データ変換
// ---------------------------------------------------------------------------

type ParsedChunk = {
  /** 同一性比較用（バイトが差し換わったら再パース） */
  bytes: Uint8Array;
  rows: TalbeDataRowType[];
};

const arrowTableToRows = (table: ArrowTable): TalbeDataRowType[] => {
  const rows: TalbeDataRowType[] = [];
  const numRows = table.numRows;
  const fields = table.schema.fields;
  for (let i = 0; i < numRows; i++) {
    const row: TalbeDataRowType = {};
    for (const field of fields) {
      const col = table.getChild(field.name);
      row[field.name] = col?.get(i) ?? null;
    }
    rows.push(row);
  }
  return rows;
};

// ---------------------------------------------------------------------------
// 型定義
// ---------------------------------------------------------------------------

interface UseVirtualTableDataOptions {
  tableName: string;
  totalRows: number;
  enabled?: boolean;
}

// ---------------------------------------------------------------------------
// フック本体
// ---------------------------------------------------------------------------

export const useVirtualTableData = ({
  tableName,
  totalRows,
  enabled = true,
}: UseVirtualTableDataOptions) => {
  // バージョン購読: チャンク追加/クリア時に再レンダーされる
  const version = useTableChunkStore((s) => s.versions[tableName] ?? 0);

  // フライト中チャンクの重複防止（Ref: 再レンダー不要）
  const fetchingChunksRef = useRef<Set<number>>(new Set());

  // パース済み行キャッシュ（Ref: バイト参照で陳腐化検知再パース）
  const parsedChunksRef = useRef<Map<number, ParsedChunk>>(new Map());

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // ---------------------------------------------------------------------------
  // チャンクフェッチ
  // ---------------------------------------------------------------------------

  const fetchChunk = useCallback(
    async (chunkIndex: number) => {
      if (!enabled) return;
      const { hasChunk, setChunk } = useTableChunkStore.getState();
      if (hasChunk(tableName, chunkIndex)) return;
      if (fetchingChunksRef.current.has(chunkIndex)) return;

      fetchingChunksRef.current.add(chunkIndex);
      setIsLoading(true);

      try {
        const startRow = chunkIndex * CHUNK_SIZE;
        const bytes = await fetchDataToArrow(tableName, startRow, CHUNK_SIZE);

        // chunk 0 のメタデータから totalRows を更新（ブートストラップ）
        if (chunkIndex === 0) {
          const arrowTable = tableFromIPC(bytes);
          const meta = arrowTable.schema.metadata;
          const metaTotalRows = parseInt(meta.get("totalRows") ?? "0", 10);
          if (metaTotalRows > 0) {
            const storeState = useTableInfosStore.getState();
            const currentInfo = storeState.tableInfos.find(
              (t) => t.tableName === tableName,
            );
            if (currentInfo && currentInfo.totalRows !== metaTotalRows) {
              storeState.updateTableInfo(tableName, {
                ...currentInfo,
                totalRows: metaTotalRows,
              });
            }
          }
        }

        setChunk(tableName, chunkIndex, bytes);
        setError(null);
      } catch (err) {
        console.error(`Failed to fetch chunk ${chunkIndex}:`, err);
        setError(err instanceof Error ? err : new Error("Unknown error"));
      } finally {
        fetchingChunksRef.current.delete(chunkIndex);
        setIsLoading(false);
      }
    },

    [tableName, enabled],
  );

  // ---------------------------------------------------------------------------
  // tableName 変更時にキャッシュフライトをリセットし chunk 0 を再フェッチ
  // ---------------------------------------------------------------------------

  useEffect(() => {
    parsedChunksRef.current.clear();
    fetchingChunksRef.current.clear();
    if (enabled) {
      void fetchChunk(0);
    }
  }, [tableName, enabled, fetchChunk]);

  // ---------------------------------------------------------------------------
  // バージョン更新時: clearTable 後（chunk 0 が消えた）なら再フェッチ
  // setChunk によるバージョン更新では chunk 0 が存在するためスキップされる
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!useTableChunkStore.getState().hasChunk(tableName, 0)) {
      parsedChunksRef.current.clear();
      fetchingChunksRef.current.clear();
      if (enabled) {
        void fetchChunk(0);
      }
    }
  }, [version, tableName, enabled, fetchChunk]);

  // ---------------------------------------------------------------------------
  // 行データ取得（VirtualTable から呼ばれる）
  // バイト参照が変わっていればパース済みキャッシュを差し換える
  // ---------------------------------------------------------------------------

  const getRowData = useCallback(
    (rowIndex: number): TalbeDataRowType | undefined => {
      const chunkIndex = Math.floor(rowIndex / CHUNK_SIZE);
      // ストア直読み（購読なし）: 再レンダーはバージョン購読が担う
      const chunkBytes = useTableChunkStore
        .getState()
        .getChunk(tableName, chunkIndex);
      if (!chunkBytes) return undefined;

      const cached = parsedChunksRef.current.get(chunkIndex);
      let rows: TalbeDataRowType[];
      if (cached && cached.bytes === chunkBytes) {
        rows = cached.rows;
      } else {
        const arrowTable = tableFromIPC(chunkBytes);
        rows = arrowTableToRows(arrowTable);
        parsedChunksRef.current.set(chunkIndex, { bytes: chunkBytes, rows });
      }

      const localIndex = rowIndex - chunkIndex * CHUNK_SIZE;
      return rows[localIndex];
    },
    [tableName],
  );

  // ---------------------------------------------------------------------------
  // プリフェッチ
  // ---------------------------------------------------------------------------

  const prefetchRange = useCallback(
    (startRow: number, endRow: number) => {
      const safeEnd = totalRows > 0 ? Math.min(endRow, totalRows - 1) : endRow;
      const firstChunk = Math.floor(startRow / CHUNK_SIZE);
      const lastChunk = Math.floor(safeEnd / CHUNK_SIZE);
      for (let i = firstChunk; i <= lastChunk; i++) {
        void fetchChunk(i);
      }
    },
    [fetchChunk, totalRows],
  );

  return { getRowData, prefetchRange, isLoading, error };
};
