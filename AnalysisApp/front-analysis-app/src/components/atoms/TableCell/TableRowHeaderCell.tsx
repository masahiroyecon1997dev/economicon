import React, { ReactNode } from 'react';

type TableRowHeaderCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export function TableRowHeaderCell({ children, onContextMenu }: TableRowHeaderCellProps) {
  return (
    <th
      className="px-4 py-2 bg-gray-200 border-b border-r text-left cursor-grab"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}
