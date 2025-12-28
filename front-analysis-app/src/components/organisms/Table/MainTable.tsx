import React from 'react';

import type { TableInfoType } from '../../../types/commonTypes';

import { TableBody } from './TableBody';
import { TableHeader } from './TableHeader';

type MainTableProps = {
  tableInfo: TableInfoType;
};

export const MainTable = ({ tableInfo }: MainTableProps) => {
  const handleContextMenu = (event: React.MouseEvent, type: string, targetId: string) => {
    console.log(event, type, targetId);
  };

  return (
    <div className="overflow-auto rounded-lg border border-brand-border bg-white shadow-sm mt-6 max-h-[calc(100vh-280px)]">
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
