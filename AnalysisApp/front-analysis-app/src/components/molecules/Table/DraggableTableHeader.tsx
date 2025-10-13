import React from 'react';
import type { ColumnType } from '../../../types/commonTypes';

type DraggableTableHeaderProps = {
  column: ColumnType;
  handleContextMenu: (event: React.MouseEvent, type: 'header', targetId: string) => void;
};

export function DraggableTableHeader({ column, handleContextMenu }: DraggableTableHeaderProps) {
  return (
    <th
      className="px-4 py-2 bg-gray-200 border-b border-r text-left cursor-grab sticky top-0 z-10"
      // onContextMenu={e => handleContextMenu(e, 'header', column.name)}
    >
      {column.name}
    </th>
  );
}
