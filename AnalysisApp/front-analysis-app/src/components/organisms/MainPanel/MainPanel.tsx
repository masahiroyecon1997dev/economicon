import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { TableInfosType } from "../../../types/stateTypes";
import { MainTable } from "../MainTable/MainTable";

type MainPanelProps = {
  tableInfos: TableInfosType;
};

export function MainPanel({ tableInfos }: MainPanelProps) {
  function clickTabChange() {}

  return (
    <div className="flex flex-col float-right w-full min-h-full">
      <div className={`h-[40px]`}>
        <div className="flex">
          {tableInfos.map((table, index) => (
            <button
              key={index}
              className={`px-4 py-2 text-white ${
                table.isActive ? "bg-indigo-600" : "hover:bg-indigo-300"
              }`}
            >
              {table.tableName}
            </button>
          ))}
        </div>
      </div>
      <div className={`flex-grow overflow-y-auto h-[calc(100vh-40-40px)]`}>
        {tableInfos.map((table, index) => (
          <MainTable key={index} tableInfo={table}></MainTable>
        ))}
      </div>
    </div>
  );
}
