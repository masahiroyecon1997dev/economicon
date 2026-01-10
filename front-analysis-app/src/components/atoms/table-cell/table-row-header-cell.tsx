import type { ReactNode } from 'react';
import React from 'react';

type TableRowHeaderCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export const TableRowHeaderCell = ({ children, onContextMenu }: TableRowHeaderCellProps) => {
  return (
    <th
      className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}
