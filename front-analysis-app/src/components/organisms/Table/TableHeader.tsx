import { useDroppable } from '@dnd-kit/core';

import React from 'react';
import type { ColumnType } from '../../../types/commonTypes';
import { TableHeaderCell } from '../../atoms/TableCell/TableHeaderCell';
import { DraggableTableHeader } from '../../molecules/Table/DraggableTableHeader';

type TableHeaderProps = {
  columns: ColumnType[];
  handleContextMenu: (event: React.MouseEvent, type: 'header', targetId: string) => void;
};

export const TableHeader = ({ columns, handleContextMenu }: TableHeaderProps) => {
  const { isOver, setNodeRef } = useDroppable({ id: 'column-droppable' });

  return (
    <thead ref={setNodeRef} className={"text-xs text-gray-700 uppercase bg-gray-50 " + (isOver ? 'bg-gray-500' : '')}>
      <tr>
        <TableHeaderCell>#</TableHeaderCell>
        {columns.map((column, i) => (
          <DraggableTableHeader
            key={i}
            column={column}
            handleContextMenu={handleContextMenu}
          />
        ))}
      </tr>
    </thead>
  );
}
