import type { ReactNode } from 'react';
import React from 'react';

type MainTableCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export const TableCell = ({ children, onContextMenu }: MainTableCellProps) => {
  return (
    <td className="px-6 py-4" onContextMenu={onContextMenu}>
      {children}
    </td>
  );
}
