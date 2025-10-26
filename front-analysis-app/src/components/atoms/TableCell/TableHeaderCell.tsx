import type { ReactNode } from 'react';
import React from 'react';

type TableHeaderCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export function TableHeaderCell({ children, onContextMenu }: TableHeaderCellProps) {
  return (
    <th
      className="px-6 py-3"
      onContextMenu={onContextMenu}
    >
      {children}
    </th>
  );
}
