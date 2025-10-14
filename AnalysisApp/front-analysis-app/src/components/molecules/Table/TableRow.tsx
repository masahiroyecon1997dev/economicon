import React from 'react';

import type { TalbeDataRowType } from '../../../types/commonTypes';
import { TableRowHeaderCell } from '../../atoms/TableCell/TableRowHeaderCell';
import { EditableTableCell } from './EditableTableCell';

type TableRowProps = {
  row: TalbeDataRowType;
  index: number;
  handleContextMenu: (event: React.MouseEvent, type: 'row' | 'cell', targetId: string) => void;
};

export function TableRow({ row, index, handleContextMenu }: TableRowProps) {
  return (
    <tr className="hover:bg-gray-50">
      <TableRowHeaderCell onContextMenu={e => handleContextMenu(e, 'row', index.toString())}>
        {index + 1}
      </TableRowHeaderCell>
      {Object.values(row).map((cell, i) => (
        <EditableTableCell
          key={i}
          rowId={index.toString()}
          value={cell}
          handleContextMenu={handleContextMenu}
        />
      ))}
    </tr>
  );
}
