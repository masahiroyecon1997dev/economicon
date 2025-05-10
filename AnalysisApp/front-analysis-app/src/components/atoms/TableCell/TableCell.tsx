import React, { ReactNode } from 'react';

type MainTableCellProps = {
  children: ReactNode;
  onContextMenu?: (event: React.MouseEvent) => void;
};

export function TableCell({ children, onContextMenu }: MainTableCellProps) {
  return (
    <td className="px-4 py-2 border-b text-sm text-gray-700" onContextMenu={onContextMenu}>
      {children}
    </td>
  );
}
