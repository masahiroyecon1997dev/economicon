import React from 'react';
import type { ColumnType } from '../../../types/commonTypes';

type DraggableTableHeaderProps = {
  column: ColumnType;
  handleContextMenu: (event: React.MouseEvent, type: 'header', targetId: string) => void;
};

export function DraggableTableHeader({ column }: DraggableTableHeaderProps) {
  return (
    <th
      className="px-6 py-3"
      // onContextMenu={e => handleContextMenu(e, 'header', column.name)}
    >
      {column.name}
    </th>
  );
}
