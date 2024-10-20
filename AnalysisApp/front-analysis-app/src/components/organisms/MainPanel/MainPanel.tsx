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
    <div className="flex flex-col h-screen">
      <div className="bg-gray-800">
        <div className="flex">
          {tableInfos.map((table, index) => (
            <button
              key={index}
              className={`px-4 py-2 text-white ${
                table.isActive ? "bg-gray-900" : "hover:bg-gray-700"
              }`}
            >
              {table.tableName}
            </button>
          ))}
        </div>
      </div>
      <div>
        <div className="flex-grow overflow-y-auto p-4">
          {tableInfos.map((table, index) => (
            <MainTable key={index} tableInfo={table}></MainTable>
          ))}
        </div>
      </div>
    </div>
  );
}
