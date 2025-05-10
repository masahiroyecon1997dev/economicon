import React from 'react';

import { HEADER_MENU_HEIGHT, TABLE_TAB_HEIGHT } from '../../../common/constant';
import { TableInfosType } from '../../../types/stateTypes';
import { MainTable } from '../Table/MainTable';

type MainPanelProps = {
  tableInfos: TableInfosType;
};

export function MainPanel({ tableInfos }: MainPanelProps) {
  // function clickTabChange() {}

  return (
    <div className="flex flex-col float-right w-full min-h-full">
      <div
        className="flex-grow overflow-y-auto"
        style={{
          height: `calc(100vh - ${HEADER_MENU_HEIGHT}px - ${TABLE_TAB_HEIGHT}px)]`,
        }}
      >
        {tableInfos.map((table, index) => (
          <MainTable key={index} tableInfo={table}></MainTable>
        ))}
      </div>
      <div style={{ height: `${HEADER_MENU_HEIGHT}px` }}>
        <div className="flex">
          {tableInfos.map((table, index) => (
            <button
              key={index}
              className={`px-4 py-2 text-white ${
                table.isActive ? 'bg-indigo-600' : 'hover:bg-indigo-300'
              }`}
            >
              {table.tableName}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
