/**
 * 仮想スクロール対応テーブルコンポーネント（刷新版）
 *
 * - チャンクデータは tableChunkStore（Zustand）から取得
 * - 未ロード行はスケルトンアニメーションで表示
 * - 列リスト変更時にチャンクキャッシュを自動無効化
 * - totalRows=0 の間はローディング表示し、chunk 0 到着後に表示切替
 */
import { useDroppable } from "@dnd-kit/core";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
} from "react";

import { getEconomiconAPI } from "../../../api/endpoints";
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
import { ColumnOperationDialog } from "../Modal/ColumnOperationDialog";
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
// 編集可能セル
// ---------------------------------------------------------------------------
const CellContent = ({
  value,
  onEdit,
}: {
  value: TableDataCellType;
  onEdit: () => void;
}) => (
  <div className="flex items-center justify-between">
    <span onClick={onEdit}>{String(value ?? "")}</span>
  </div>
);

const TableInputText = ({
  value,
  onChange,
  onBlur,
  className,
}: {
  value: TableDataCellType;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
  className?: string;
}) => (
  <input
    type="text"
    className={cn("w-full rounded border p-1", className)}
    value={value?.toString() ?? ""}
    onChange={onChange}
    onBlur={onBlur}
    autoFocus
  />
);

const EditableCell = ({ value }: { value: TableDataCellType }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [cellValue, setCellValue] = useState<TableDataCellType>(value);
  return (
    <div className="px-3 py-0.5 overflow-hidden">
      {isEditing ? (
        <TableInputText
          value={cellValue}
          onChange={(e) => setCellValue(e.target.value)}
          onBlur={() => setIsEditing(false)}
        />
      ) : (
        <div className="truncate text-xs text-gray-700">
          <CellContent value={cellValue} onEdit={() => setIsEditing(true)} />
        </div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// メインコンポーネント
// ---------------------------------------------------------------------------
export const VirtualTable = ({ tableInfo }: VirtualTableProps) => {
  // useReactTable が返す関数はメモ化不可のため React Compiler をスキップ
  "use no memo";

  const { tableName, columnList, totalRows } = tableInfo;
  const parentRef = useRef<HTMLDivElement>(null);

  // ドラッグ&ドロップ
  const { isOver, setNodeRef } = useDroppable({ id: "column-droppable" });

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

  // 列ヘッダーのアクション受信
  const handleColumnAction = useCallback(
    (col: ColumnType, op: ColumnOperation) => {
      if (op === "sort_asc" || op === "sort_desc") {
        void getEconomiconAPI()
          .sortColumns({
            tableName,
            sortColumns: [
              { columnName: col.name, ascending: op === "sort_asc" },
            ],
          })
          .then(() => {
            // チャンクキャッシュを無効化してデータを再取得
            invalidateTable(tableName, {});
          });
      } else {
        setDialogState({ open: true, operation: op, column: col });
      }
    },
    [tableName, invalidateTable],
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
    // 列名の描画幅から幅を計算（バッジ+ギャップ+メニュー+パディング ≈ 68px）
    const HEADER_OVERHEAD = 68;
    const MAX_COL_WIDTH = 170;
    const MIN_COL_WIDTH = 80;

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
          <div className="group flex items-center gap-1.5 min-w-0">
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
            <ColumnContextMenu
              column={column}
              onAction={(op) => handleColumnAction(column, op)}
            />
          </div>
        ),
        cell: ({ row }) => {
          const rowData = getRowData(row.index);
          if (!rowData) return <SkeletonCell />;
          return (
            <EditableCell value={rowData[column.name] as TableDataCellType} />
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

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    // TODO: コンテキストメニュー
  };

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
            データを読み込んでいます
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 通常レンダリング
  // ---------------------------------------------------------------------------
  return (
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
          <thead
            ref={setNodeRef}
            className={cn(
              "sticky top-0 z-10 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800",
              isOver && "bg-gray-500",
            )}
          >
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-3 py-3 relative select-none overflow-hidden"
                    style={{ width: header.getSize() }}
                    onContextMenu={handleContextMenu}
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
                  onContextMenu={handleContextMenu}
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
          読み込み中
        </div>
      )}

      {error && (
        <div className="fixed bottom-4 right-4 z-50 rounded-full bg-red-500 px-3 py-1.5 text-xs font-medium text-white shadow-md">
          エラー: {error.message}
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
  );
};
