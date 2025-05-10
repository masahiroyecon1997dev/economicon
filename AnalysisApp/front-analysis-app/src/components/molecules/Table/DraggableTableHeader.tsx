import React from 'react';
import { ColumnType } from '../../../types/commonTypes';

type DraggableTableHeaderProps = {
  column: ColumnType;
  handleContextMenu: (event: React.MouseEvent, type: 'header', targetId: string) => void;
};

export function DraggableTableHeader({ column, handleContextMenu }: DraggableTableHeaderProps) {
  return (
    <th
      className="px-4 py-2 bg-gray-200 border-b border-r text-left cursor-grab sticky top-0 z-10"
      onContextMenu={e => handleContextMenu(e, 'header', column.id)}
    >
      {column.name}
    </th>
  );
}
