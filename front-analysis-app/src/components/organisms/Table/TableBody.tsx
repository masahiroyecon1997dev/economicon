import React from 'react';
import type { TableDataType } from '../../../types/commonTypes';
import { TableRow } from '../../molecules/Table/TableRow';

type TableBodyProps = {
  tableData: TableDataType;
  handleContextMenu: (event: React.MouseEvent, type: 'row' | 'cell', targetId: string) => void;
};

export const TableBody = ({ tableData, handleContextMenu }: TableBodyProps) => {
  return (
    <tbody>
      {tableData?.map((row, index) => (
        <TableRow key={index} row={row} index={index} handleContextMenu={handleContextMenu} />
      ))}
    </tbody>
  );
}
