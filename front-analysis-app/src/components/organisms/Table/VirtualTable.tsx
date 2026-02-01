/**
 * 仮想スクロール対応のテーブルコンポーネント
 * TanStack TableとTanStack Virtualを使用
 */
import { useDroppable } from '@dnd-kit/core';
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import React, { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';

import { cn } from '../../../functions/utils';
import { useVirtualTableData } from '../../../hooks/useVirtualTableData';
import type { ColumnType, TableDataCellType, TableInfoType, TalbeDataRowType } from '../../../types/commonTypes';

type VirtualTableProps = {
  tableInfo: TableInfoType;
};

const OVERSCAN_COUNT = 50; // 上下に余分に描画する行数（スムーズなスクロールのために増やす）

// 内部コンポーネント: CellContent
function CellContent({ value, onEdit }: { value: TableDataCellType; onEdit: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <span onClick={onEdit}>{String(value ?? '')}</span>
    </div>
  );
}

// 内部コンポーネント: TableInputText
function TableInputText({
  value,
  onChange,
  onBlur,
  className
}: {
  value: TableDataCellType;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
  className?: string;
}) {
  return (
    <input
      type="text"
      className={cn("w-full border rounded p-1", className)}
      value={value?.toString() ?? ''}
      onChange={onChange}
      onBlur={onBlur}
      autoFocus
    />
  );
}

// 内部コンポーネント: EditableCell
function EditableCell({ value }: { value: TableDataCellType }) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [cellValue, setCellValue] = useState<TableDataCellType>(value);

  function handleEditCell() {
    setIsEditing(true);
  }

  function handleEditingCell(event: ChangeEvent<HTMLInputElement>) {
    setCellValue(event.target.value);
  }

  function handleSaveCell() {
    setIsEditing(false);
    // TODO: API呼び出しでセル値を保存
  }

  return (
    <div className="px-6 py-4">
      {isEditing ? (
        <TableInputText
          value={cellValue}
          onChange={e => handleEditingCell(e)}
          onBlur={() => handleSaveCell()}
        />
      ) : (
        <CellContent value={cellValue} onEdit={() => handleEditCell()} />
      )}
    </div>
  );
}

export const VirtualTable = ({ tableInfo }: VirtualTableProps) => {
  const { tableName, columnList, totalRows } = tableInfo;
  const parentRef = useRef<HTMLDivElement>(null);

  // ドラッグ&ドロップ用
  const { isOver, setNodeRef } = useDroppable({ id: 'column-droppable' });

  // 仮想テーブルデータフック
  const { getRowData, prefetchRange, isLoading, error } = useVirtualTableData({
    tableName,
    totalRows,
    enabled: true,
  });

  // TanStack Tableの列定義
  const columns = useMemo<ColumnDef<TalbeDataRowType>[]>(() => {
    const cols: ColumnDef<TalbeDataRowType>[] = [
      {
        id: 'rowNumber',
        header: '#',
        cell: ({ row }) => (
          <div className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">
            {row.index + 1}
          </div>
        ),
        size: 80,
      },
    ];

    // データ列の追加
    columnList.forEach((column: ColumnType) => {
      cols.push({
        accessorKey: column.name,
        header: column.name,
        cell: ({ getValue }) => <EditableCell value={getValue() as TableDataCellType} />,
      });
    });

    return cols;
  }, [columnList]);

  // 仮想化のための行データ（実際のデータはgetRowDataから取得）
  const virtualData = useMemo(() => {
    return Array.from({ length: totalRows }, (_, i) => {
      const rowData = getRowData(i);
      return rowData ?? ({} as TalbeDataRowType);
    });
  }, [totalRows, getRowData]);

  // TanStack Tableの設定
  const table = useReactTable({
    data: virtualData,
    columns,
    getCoreRowModel: getCoreRowModel(),
    enableRowSelection: false,
    enableColumnResizing: false,
  });

  const { rows } = table.getRowModel();

  // TanStack Virtualの設定
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 56, // 行の高さ（px）
    overscan: OVERSCAN_COUNT,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();

  // スクロール時に必要な範囲をプリフェッチ
  useEffect(() => {
    if (virtualRows.length > 0) {
      const firstRow = virtualRows[0].index;
      const lastRow = virtualRows[virtualRows.length - 1].index;

      // 前後の部分に余裕を持って動的フェッチ（+30行以上のバッファを確保）
      const PREFETCH_BUFFER = 50;
      const prefetchStart = Math.max(0, firstRow - PREFETCH_BUFFER);
      const prefetchEnd = Math.min(totalRows - 1, lastRow + PREFETCH_BUFFER);

      prefetchRange(prefetchStart, prefetchEnd);
    }
  }, [virtualRows, totalRows, prefetchRange]);

  // 初期ロード時に最初のチャンクをフェッチ
  useEffect(() => {
    prefetchRange(0, Math.min(OVERSCAN_COUNT * 2, totalRows - 1));
  }, [tableName, totalRows, prefetchRange]);

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    // TODO: コンテキストメニューの実装
    console.log('Context menu', event);
  };

  // 仮想アイテムの総高さ
  const totalSize = rowVirtualizer.getTotalSize();

  // パディングトップ（最初の仮想アイテムまでの高さ）
  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0;

  // パディングボトム（最後の仮想アイテム以降の高さ）
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - virtualRows[virtualRows.length - 1].end
      : 0;

  return (
    <div
      ref={parentRef}
      className="overflow-auto rounded-lg border border-brand-border bg-white shadow-sm mt-6 max-h-[calc(100vh-280px)]"
    >
      <div style={{ height: `${totalSize}px`, position: 'relative' }}>
        <table className="w-full text-sm text-left text-gray-500">
          <thead
            ref={setNodeRef}
            className={cn(
              "sticky top-0 z-10 text-xs text-gray-700 uppercase bg-gray-50",
              isOver && 'bg-gray-500'
            )}
          >
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3"
                    style={{ width: header.getSize() }}
                    onContextMenu={handleContextMenu}
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
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
                  className="bg-white border-b"
                  style={{
                    height: `${virtualRow.size}px`,
                  }}
                  onContextMenu={handleContextMenu}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="p-0">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
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
      {isLoading && (
        <div className="absolute bottom-4 right-4 bg-blue-500 text-white px-3 py-1 rounded text-xs">
          読み込み中...
        </div>
      )}
      {error && (
        <div className="absolute bottom-4 right-4 bg-red-500 text-white px-3 py-1 rounded text-xs">
          エラー: {error.message}
        </div>
      )}
    </div>
  );
};
