import { useDroppable } from '@dnd-kit/core';
import React, { useState, type ChangeEvent } from 'react';

import { cn } from '../../../lib/utils/helpers';
import type { ColumnType, TableDataCellType, TableInfoType, TalbeDataRowType } from '../../../types/commonTypes';

type MainTableProps = {
  tableInfo: TableInfoType;
};

// 内部コンポーネント: CellContent
function CellContent({ value, onEdit }: { value: TableDataCellType; onEdit: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <span onClick={onEdit}>{value}</span>
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
      value={value?.toString()}
      onChange={onChange}
      onBlur={onBlur}
      autoFocus
    />
  );
}

// 内部コンポーネント: TableCell
function TableCell({
  children,
  onContextMenu
}: {
  children: React.ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void
}) {
  return (
    <td className="px-6 py-4" onContextMenu={onContextMenu}>
      {children}
    </td>
  );
}

// 内部コンポーネント: EditableTableCell
function EditableTableCell({
  value,
  handleContextMenu
}: {
  value: TableDataCellType;
  handleContextMenu: (event: React.MouseEvent, type: 'cell', targetId: string) => void;
}) {
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
  }

  return (
    <TableCell
      onContextMenu={e =>
        handleContextMenu(e, 'cell', `rowId-columnId`)
      }
    >
      {isEditing ? (
        <TableInputText
          value={cellValue}
          onChange={e => handleEditingCell(e)}
          onBlur={() => handleSaveCell()}
        />
      ) : (
        <CellContent value={value} onEdit={() => handleEditCell()} />
      )}
    </TableCell>
  );
}

// 内部コンポーネント: TableRowHeaderCell
function TableRowHeaderCell({
  children,
  onContextMenu
}: {
  children: React.ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
}) {
  return (
    <th
      className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}

// 内部コンポーネント: TableRow
function TableRow({
  row,
  index,
  handleContextMenu
}: {
  row: TalbeDataRowType;
  index: number;
  handleContextMenu: (event: React.MouseEvent, type: 'row' | 'cell', targetId: string) => void;
}) {
  return (
    <tr className="bg-white border-b">
      <TableRowHeaderCell onContextMenu={e => handleContextMenu(e, 'row', index.toString())}>
        {index + 1}
      </TableRowHeaderCell>
      {Object.values(row).map((cell, i) => (
        <EditableTableCell
          key={i}
          value={cell}
          handleContextMenu={handleContextMenu}
        />
      ))}
    </tr>
  );
}

// 内部コンポーネント: DraggableTableHeader
function DraggableTableHeader({ column }: { column: ColumnType }) {
  return (
    <th className="px-6 py-3">
      {column.name}
    </th>
  );
}

// 内部コンポーネント: TableHeaderCell
function TableHeaderCell({
  children,
  onContextMenu
}: {
  children: React.ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
}) {
  return (
    <th
      className="px-6 py-3"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}

export const MainTable = ({ tableInfo }: MainTableProps) => {
  const { isOver, setNodeRef } = useDroppable({ id: 'column-droppable' });

  const handleContextMenu = (event: React.MouseEvent, type: string, targetId: string) => {
    console.log(event, type, targetId);
  };

  return (
    <div className="overflow-auto rounded-lg border border-brand-border bg-white shadow-sm mt-6 max-h-[calc(100vh-280px)]">
      <table className="w-full text-sm text-left text-gray-500">
        <thead ref={setNodeRef} className={"sticky top-0 z-10 text-xs text-gray-700 uppercase bg-gray-50 " + (isOver ? 'bg-gray-500' : '')}>
          <tr>
            <TableHeaderCell>#</TableHeaderCell>
            {tableInfo.columnList.map((column, i) => (
              <DraggableTableHeader
                key={i}
                column={column}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {tableInfo.data?.map((row, index) => (
            <TableRow key={index} row={row} index={index} handleContextMenu={handleContextMenu} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
