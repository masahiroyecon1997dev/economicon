import React, { ChangeEvent, useState } from 'react';
import { TableDataCellType } from '../../../types/commonTypes';
import { TableInputText } from '../../atoms/Input/TableInputText';
import { TableCell } from '../../atoms/TableCell/TableCell';
import { CellContent } from './CellContent';

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
