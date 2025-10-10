import React from 'react';

import type { TableInfoType } from '../../../types/commonTypes';

import { TableBody } from './TableBody';
import { TableHeader } from './TableHeader';

type MainTableProps = {
  tableInfo: TableInfoType;
};

export function MainTable({ tableInfo }: MainTableProps) {
  function handleContextMenu(event: React.MouseEvent, type: string, targetId: string) {
    console.log(event, type, targetId);
  }

  return (
    <div>
      <table className="border-separate border-spacing-0 border-l border-r bg-white border-gray-300 table-auto">
        <TableHeader
          columns={tableInfo.columnList}
          handleContextMenu={handleContextMenu}
        ></TableHeader>
        <TableBody tableData={tableInfo.data} handleContextMenu={handleContextMenu}></TableBody>
      </table>
    </div>
  );
}
