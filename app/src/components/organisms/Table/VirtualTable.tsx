/**
 * 仮想スクロール対応テーブルコンポーネント（刷新版）
 *
 * - チャンクデータは tableChunkStore（Zustand）から取得
 * - 未ロード行はスケルトンアニメーションで表示
 * - 列リスト変更時にチャンクキャッシュを自動無効化
 * - totalRows=0 の間はローディング表示し、chunk 0 到着後に表示切替
 */
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  horizontalListSortingStrategy,
} from "@dnd-kit/sortable";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type ColumnSizingState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getEconomiconAppAPI } from "../../../api/endpoints";
import { useDragColumnReorder } from "../../../hooks/useDragColumnReorder";
import { useVirtualTableData } from "../../../hooks/useVirtualTableData";
import { getPolarsTypeColor } from "../../../lib/utils/columnTypeColor";
import { cn } from "../../../lib/utils/helpers";
import { useTableChunkStore } from "../../../stores/tableChunkStore";
import { useTableInfosStore } from "../../../stores/tableInfos";
import type {
  ColumnType,
  TableDataCellType,
  TableInfoType,
  TalbeDataRowType,
} from "../../../types/commonTypes";
import { DraggableColumnHeader } from "../../molecules/Table/DraggableColumnHeader";
import { ColumnOperationDialog } from "../Dialog/ColumnOperationDialog";
import { ColumnContextMenu, type ColumnOperation } from "./ColumnContextMenu";

type VirtualTableProps = {
  tableInfo: TableInfoType;
};

const OVERSCAN_COUNT = 15;

// ---------------------------------------------------------------------------
// 列名の描画幅計測（全角文字・半角文字を区別）
// ---------------------------------------------------------------------------
const measureColumnName = (name: string): number => {
  let width = 0;
  for (const char of name) {
    const code = char.codePointAt(0) ?? 0;
    // ひらがな・カタカナ・漢字・全角記号等は半角の約2倍幅
    const isFullWidth =
      (code >= 0x3000 && code <= 0x9fff) || // CJK + ひらがな + カタカナ
      (code >= 0xac00 && code <= 0xd7af) || // ハングル音節
      (code >= 0xf900 && code <= 0xfaff) || // CJK 互換漢字
      (code >= 0xff01 && code <= 0xff60) || // 全角英数字・記号
      (code >= 0xffe0 && code <= 0xffe6); // 全角記号
    width += isFullWidth ? 13 : 7;
  }
  return width;
};

// ---------------------------------------------------------------------------
// スケルトンセル
// ---------------------------------------------------------------------------
const SkeletonCell = () => (
  <div className="px-3 py-1">
    <div className="h-3 w-3/4 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
  </div>
);

// ---------------------------------------------------------------------------
// 読み取り専用セル
// ---------------------------------------------------------------------------
const ReadOnlyCell = ({ value }: { value: TableDataCellType }) => (
  <div className="px-3 py-0.5 overflow-hidden">
    <div className="truncate text-xs text-gray-700 dark:text-gray-300">
      {String(value ?? "")}
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// メインコンポーネント
// ---------------------------------------------------------------------------
export const VirtualTable = ({ tableInfo }: VirtualTableProps) => {
  // useReactTable が返す関数はメモ化不可のため React Compiler をスキップ
  "use no memo";
  const { t } = useTranslation();

  const { tableName, columnList, totalRows } = tableInfo;
  const parentRef = useRef<HTMLDivElement>(null);

  // 列幅の永続化: 列の追加・削除があっても残存列の幅は保持する
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>({});

  // ドラッグ&ドロップ（列移動）
  const {
    activeColumnId,
    dragErrorKey,
    onDragStart,
    onDragEnd,
    clearDragError,
  } = useDragColumnReorder({ tableName, columnList });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
  );

  // バージョン購読: チャンク更新時に再レンダー（useVirtualTableData 内でも購読しているが
  // VirtualTable 自体も購読して columns の cell closure を最新化する）
  useTableChunkStore((s) => s.versions[tableName] ?? 0);

  // データフック（フェッチプリフェッチ）
  const { getRowData, prefetchRange, isLoading, error } = useVirtualTableData({
    tableName,
    totalRows,
    enabled: true,
  });

  // ---------------------------------------------------------------------------
  // 列リスト変更時にキャッシュを無効化
  // ---------------------------------------------------------------------------
  const prevColumnKeyRef = useRef<string>("");
  const invalidateTable = useTableInfosStore((s) => s.invalidateTable);

  // ---------------------------------------------------------------------------
  // 列操作ダイアログ状態
  // ---------------------------------------------------------------------------
  const [dialogState, setDialogState] = useState<{
    open: boolean;
    operation: ColumnOperation | null;
    column: ColumnType | null;
  }>({ open: false, operation: null, column: null });

  const [sortError, setSortError] = useState<string | null>(null);

  // DndContext イベントハンドラー（useCallback で安定化）
  const handleDragStart = useCallback(
    (event: DragStartEvent) => onDragStart(event),
    [onDragStart],
  );
  const handleDragEnd = useCallback(
    (event: DragEndEvent) => onDragEnd(event),
    [onDragEnd],
  );

  // 列ヘッダーのアクション受信
  const handleColumnAction = useCallback(
    async (col: ColumnType, op: ColumnOperation) => {
      if (op === "sort_asc" || op === "sort_desc") {
        setSortError(null);
        try {
          await getEconomiconAppAPI().sortColumns({
            tableName,
            sortColumns: [
              { columnName: col.name, ascending: op === "sort_asc" },
            ],
          });
          // チャンクキャッシュを無効化してデータを再取得
          invalidateTable(tableName, {});
        } catch (e) {
          setSortError(e instanceof Error ? e.message : t("Table.SortError"));
        }
      } else {
        setDialogState({ open: true, operation: op, column: col });
      }
    },
    [tableName, invalidateTable, t],
  );

  useEffect(() => {
    const key = columnList.map((c) => c.name).join(",");
    if (prevColumnKeyRef.current && prevColumnKeyRef.current !== key) {
      // 列が変わったらバイナリキャッシュを無効化
      invalidateTable(tableName, { columnList });
      // 削除された列のサイズキャッシュを除去（残存する列は幅を保持）
      const activeIds = new Set(columnList.map((c) => c.name));
      setColumnSizing((prev) => {
        const next: ColumnSizingState = {};
        for (const [k, v] of Object.entries(prev)) {
          if (activeIds.has(k)) next[k] = v;
        }
        return next;
      });
    }
    prevColumnKeyRef.current = key;
  }, [columnList, tableName, invalidateTable]);

  // ---------------------------------------------------------------------------
  // TanStack Table 列定義
  // ---------------------------------------------------------------------------
  const columns = useMemo<ColumnDef<TalbeDataRowType>[]>(() => {
    const cols: ColumnDef<TalbeDataRowType>[] = [
      {
        id: "rowNumber",
        header: "#",
        cell: ({ row }) => (
          <div className="px-3 py-0.5 font-medium text-gray-400 whitespace-nowrap text-xs">
            {row.index + 1}
          </div>
        ),
        size: 48,
        enableResizing: false,
      },
    ];
    // 列名の描画幅から幅を計算
    const HEADER_OVERHEAD = 70;
    const MAX_COL_WIDTH = 250;
    const MIN_COL_WIDTH = 140;

    columnList.forEach((column: ColumnType) => {
      const typeColor = getPolarsTypeColor(column.type);
      const calculatedSize = Math.min(
        MAX_COL_WIDTH,
        Math.max(
          MIN_COL_WIDTH,
          Math.round(HEADER_OVERHEAD + measureColumnName(column.name)),
        ),
      );
      cols.push({
        id: column.name,
        accessorKey: column.name,
        size: calculatedSize,
        minSize: MIN_COL_WIDTH,
        header: () => (
          <DraggableColumnHeader id={column.name}>
            <ColumnContextMenu
              column={column}
              onAction={(op) => handleColumnAction(column, op)}
            >
              <span
                className={cn(
                  "shrink-0 px-1 py-0.5 rounded text-[10px] font-bold font-mono leading-none",
                  typeColor.bg,
                  typeColor.text,
                )}
              >
                {typeColor.label}
              </span>
              <span className="truncate">{column.name}</span>
            </ColumnContextMenu>
          </DraggableColumnHeader>
        ),
        cell: ({ row }) => {
          const rowData = getRowData(row.index);
          if (!rowData) return <SkeletonCell />;
          return (
            <ReadOnlyCell value={rowData[column.name] as TableDataCellType} />
          );
        },
      });
    });
    return cols;
    // getRowData は tableName のみに依存するため、安定している
  }, [columnList, getRowData, handleColumnAction]);

  // ---------------------------------------------------------------------------
  // テーブルデータ（行数分のプレースホルダー）
  // ---------------------------------------------------------------------------
  const virtualData = useMemo(
    () => new Array(totalRows).fill(null) as TalbeDataRowType[],
    [totalRows],
  );

  const table = useReactTable({
    data: virtualData,
    columns,
    state: { columnSizing },
    onColumnSizingChange: setColumnSizing,
    getCoreRowModel: getCoreRowModel(),
    enableRowSelection: false,
    enableColumnResizing: true,
    columnResizeMode: "onChange",
  });

  const { rows } = table.getRowModel();

  // ---------------------------------------------------------------------------
  // TanStack Virtual
  // ---------------------------------------------------------------------------
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 28,
    overscan: OVERSCAN_COUNT,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();

  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - virtualRows[virtualRows.length - 1].end
      : 0;

  // ---------------------------------------------------------------------------
  // スクロール時プリフェッチ
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (virtualRows.length === 0 || totalRows === 0) return;
    const firstRow = virtualRows[0].index;
    const lastRow = virtualRows[virtualRows.length - 1].index;
    const BUFFER = 50;
    prefetchRange(
      Math.max(0, firstRow - BUFFER),
      Math.min(totalRows - 1, lastRow + BUFFER),
    );
  }, [virtualRows, totalRows, prefetchRange]);

  // ---------------------------------------------------------------------------
  // ローディング状態（totalRows 未確定）
  // ---------------------------------------------------------------------------
  if (totalRows === 0) {
    return (
      <div className="overflow-hidden rounded-lg border border-brand-border bg-white dark:bg-gray-900 shadow-sm h-full flex flex-col">
        <table className="w-full text-sm text-left text-gray-500 dark:text-gray-400">
          <thead className="sticky top-0 z-10 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-3 py-3">#</th>
              {columnList.map((col) => (
                <th key={col.name} className="px-3 py-3">
                  {col.name}
                </th>
              ))}
            </tr>
          </thead>
        </table>
        <div className="flex items-center justify-center py-12 text-sm text-gray-400">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 dark:border-gray-600 border-t-brand-primary" />
            {t("Table.LoadingData")}
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 通常レンダリング
  // ---------------------------------------------------------------------------

  // SortableContext に渡す ID リスト（# 列は除外）
  const sortableIds = columnList.map((c) => c.name);

  // ドラッグ中の列の情報（DragOverlay 表示用）
  const activeColumn = activeColumnId
    ? columnList.find((c) => c.name === activeColumnId)
    : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div
        ref={parentRef}
        className="overflow-auto rounded-lg border border-brand-border bg-white dark:bg-gray-900 shadow-sm h-full"
        style={{ willChange: "scroll-position" }}
      >
        <div style={{ height: `${totalSize}px`, position: "relative" }}>
          <table
            className="text-sm text-left text-gray-500 table-fixed"
            style={{ width: table.getCenterTotalSize() }}
          >
            <thead className="sticky top-0 z-10 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  <SortableContext
                    items={sortableIds}
                    strategy={horizontalListSortingStrategy}
                  >
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-3 py-3 relative select-none overflow-hidden"
                        style={{ width: header.getSize() }}
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext(),
                            )}
                        {header.column.getCanResize() && (
                          <div
                            onMouseDown={header.getResizeHandler()}
                            onTouchStart={header.getResizeHandler()}
                            className={cn(
                              "absolute right-0 top-0 h-full w-1 cursor-col-resize bg-gray-300 dark:bg-gray-600 opacity-0 hover:opacity-100 active:opacity-100 transition-opacity",
                              header.column.getIsResizing() &&
                                "opacity-100 bg-brand-primary",
                            )}
                          />
                        )}
                      </th>
                    ))}
                  </SortableContext>
                </tr>
              ))}
            </thead>
            <tbody>
              {paddingTop > 0 && (
                <tr>
                  <td style={{ height: `${paddingTop}px` }} />
                </tr>
              )}
              {virtualRows.map((virtualRow) => {
                const row = rows[virtualRow.index];
                return (
                  <tr
                    key={row.id}
                    className="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/70"
                    style={{ height: `${virtualRow.size}px` }}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="p-0">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })}
              {paddingBottom > 0 && (
                <tr>
                  <td style={{ height: `${paddingBottom}px` }} />
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* ローディングインジケーター（チャンク取得中） */}
        {isLoading && (
          <div className="fixed bottom-4 right-4 z-50 flex items-center gap-1.5 rounded-full bg-brand-primary/90 px-3 py-1.5 text-xs font-medium text-white shadow-md">
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            {t("Table.FetchingChunk")}
          </div>
        )}

        {error && (
          <div className="fixed bottom-4 right-4 z-50 rounded-full bg-red-500 px-3 py-1.5 text-xs font-medium text-white shadow-md">
            {t("Table.FetchError", { message: error.message })}
          </div>
        )}

        {(sortError ?? dragErrorKey) && (
          <div
            className="fixed bottom-4 right-4 z-50 rounded-full bg-red-500 px-3 py-1.5 text-xs font-medium text-white shadow-md cursor-pointer"
            onClick={() => {
              setSortError(null);
              clearDragError();
            }}
          >
            {sortError ?? (dragErrorKey ? t(dragErrorKey) : null)}
          </div>
        )}

        <ColumnOperationDialog
          open={dialogState.open}
          onOpenChange={(open) => setDialogState((prev) => ({ ...prev, open }))}
          operation={dialogState.operation}
          tableName={tableName}
          column={dialogState.column}
          onSuccess={(updatedList) => {
            invalidateTable(tableName, { columnList: updatedList });
            setDialogState({ open: false, operation: null, column: null });
          }}
        />
      </div>

      {/* ドラッグ中のゴーストヘッダー */}
      <DragOverlay>
        {activeColumn && (
          <div className="flex items-center gap-1 px-3 py-3 rounded shadow-lg bg-white dark:bg-gray-800 border border-brand-border text-xs font-semibold text-gray-700 dark:text-gray-200 opacity-90 cursor-grabbing">
            <span className="truncate">{activeColumn.name}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
};
