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
import {
  useEffect,
  useMemo,
  useRef,
  type Dispatch,
  type SetStateAction,
} from "react";
import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils/helpers";
import type { TalbeDataRowType } from "@/types/commonTypes";

const OVERSCAN_COUNT = 15;
const PREFETCH_BUFFER = 50;

type VirtualTableCompilerBoundaryProps = {
  columns: ColumnDef<TalbeDataRowType>[];
  totalRows: number;
  columnSizing: ColumnSizingState;
  setColumnSizing: Dispatch<SetStateAction<ColumnSizingState>>;
  prefetchRange: (startRow: number, endRow: number) => void;
  sortableIds: string[];
  isLoading: boolean;
  error: Error | null;
  sortError: string | null;
  dragErrorKey: string | null;
  clearDragError: () => void;
  clearSortError: () => void;
};

export const VirtualTableCompilerBoundary = ({
  columns,
  totalRows,
  columnSizing,
  setColumnSizing,
  prefetchRange,
  sortableIds,
  isLoading,
  error,
  sortError,
  dragErrorKey,
  clearDragError,
  clearSortError,
}: VirtualTableCompilerBoundaryProps) => {
  const { t } = useTranslation();
  const parentRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    if (virtualRows.length === 0 || totalRows === 0) return;
    const firstRow = virtualRows[0].index;
    const lastRow = virtualRows[virtualRows.length - 1].index;

    prefetchRange(
      Math.max(0, firstRow - PREFETCH_BUFFER),
      Math.min(totalRows - 1, lastRow + PREFETCH_BUFFER),
    );
  }, [virtualRows, totalRows, prefetchRange]);

  return (
    <div
      ref={parentRef}
      data-testid="virtual-table-grid"
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
            clearSortError();
            clearDragError();
          }}
        >
          {sortError ?? (dragErrorKey ? t(dragErrorKey) : null)}
        </div>
      )}
    </div>
  );
};
