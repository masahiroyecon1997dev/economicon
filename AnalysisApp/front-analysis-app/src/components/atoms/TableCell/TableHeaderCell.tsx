import type { ReactNode } from 'react';
import React from 'react';

type TableHeaderCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export function TableHeaderCell({ children, onContextMenu }: TableHeaderCellProps) {
  return (
    <th
      className="px-4 py-2 bg-gray-200 border-b border-r text-left cursor-grab sticky top-0 z-10"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}
