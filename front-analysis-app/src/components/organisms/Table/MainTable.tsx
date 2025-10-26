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
    <div className="overflow-x-auto rounded-lg border border-brand-border bg-white shadow-sm mt-6">
      <table className="w-full text-sm text-left text-gray-500">
        <TableHeader
          columns={tableInfo.columnList}
          handleContextMenu={handleContextMenu}
        ></TableHeader>
        <TableBody tableData={tableInfo.data} handleContextMenu={handleContextMenu}></TableBody>
      </table>
    </div>
  );
}
