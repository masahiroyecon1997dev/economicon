import React, { useState, type ChangeEvent } from 'react';

import type { TableDataCellType } from '../../../types/commonTypes';
import { TableInputText } from '../../atoms/Input/table-input-text';
import { TableCell } from '../../atoms/table-cell/table-cell';
import { CellContent } from './cell-content';

type EditableTableCellProps = {
  rowId: string;
  value: TableDataCellType;
  handleContextMenu: (event: React.MouseEvent, type: 'cell', targetId: string) => void;
};

export function EditableTableCell({ value, handleContextMenu }: EditableTableCellProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [cellValue, setCellValue] = useState<TableDataCellType>(value);

  function handleEditCell() {
    setIsEditing(true);
  }

  function handleEditingCell(event: ChangeEvent<HTMLInputElement>) {
    setCellValue(event.target.value);
  }

  function handleSaveCell() {
    setIsEditing(false);
  }

  return (
    <TableCell
      onContextMenu={e =>
        handleContextMenu(e, 'cell', `<span class="math-inline">{rowId}-</span>{columnId}`)
      }
    >
      {isEditing ? (
        <TableInputText
          value={cellValue}
          onChange={e => handleEditingCell(e)}
          onBlur={() => handleSaveCell()}
        />
      ) : (
        <CellContent value={value} onEdit={() => handleEditCell()} />
      )}
    </TableCell>
  );
}
