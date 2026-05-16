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
import { type ColumnDef, type ColumnSizingState } from "@tanstack/react-table";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getEconomiconAppAPI } from "@/api/endpoints";
import { DraggableColumnHeader } from "@/components/molecules/Table/DraggableColumnHeader";
import { ColumnOperationDialog } from "@/components/organisms/Dialog/ColumnOperationDialog";
import {
  ColumnContextMenu,
  type ColumnOperation,
} from "@/components/organisms/Table/ColumnContextMenu";
import { VirtualTableCompilerBoundary } from "@/components/organisms/Table/VirtualTableCompilerBoundary";
import { useDragColumnReorder } from "@/hooks/useDragColumnReorder";
import { useVirtualTableData } from "@/hooks/useVirtualTableData";
import { getPolarsTypeColor } from "@/lib/utils/columnTypeColor";
import { cn } from "@/lib/utils/helpers";
import { useTableChunkStore } from "@/stores/tableChunkStore";
import { useTableInfosStore } from "@/stores/tableInfos";
import type {
  ColumnType,
  TableDataCellType,
  TableInfoType,
  TalbeDataRowType,
} from "@/types/commonTypes";

type VirtualTableProps = {
  tableInfo: TableInfoType;
};

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
  const { t } = useTranslation();

  const { tableName, columnList, totalRows } = tableInfo;

  // 列幅の永続化: 列の追加・削除があっても残存列の幅は保持する
  const [rawColumnSizing, setColumnSizing] = useState<ColumnSizingState>({});

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
  const columnSizing = useMemo(() => {
    const activeIds = new Set(columnList.map((column) => column.name));
    const next: ColumnSizingState = {};

    for (const [key, value] of Object.entries(rawColumnSizing)) {
      if (activeIds.has(key)) {
        next[key] = value;
      }
    }

    return next;
  }, [columnList, rawColumnSizing]);

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
      <VirtualTableCompilerBoundary
        columns={columns}
        totalRows={totalRows}
        columnSizing={columnSizing}
        setColumnSizing={setColumnSizing}
        prefetchRange={prefetchRange}
        sortableIds={sortableIds}
        isLoading={isLoading}
        error={error}
        sortError={sortError}
        dragErrorKey={dragErrorKey}
        clearDragError={clearDragError}
        clearSortError={() => setSortError(null)}
      />

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
