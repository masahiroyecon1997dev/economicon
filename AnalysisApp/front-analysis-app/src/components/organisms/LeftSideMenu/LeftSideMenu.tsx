import React, { useState, useEffect, Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";
import { TableInfosType, TableListType } from "../../../types/stateTypes";
import { getTableInfo } from "../../../functiom/internalFunctions";

type LeftSideMenuProps = {
  tableInfos: TableInfosType;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
  tableList: TableListType;
};

export function LeftSideMenu({
  tableInfos,
  setTableInfos,
  tableList,
}: LeftSideMenuProps) {
  const { t } = useTranslation();

  async function clickTableName(tableName: string) {
    const sameTableNameInfos = tableInfos.filter(
      (tableInfo) => tableInfo.tableName === tableName
    );
    if (sameTableNameInfos.length > 0) {
      setTableInfos((preTableInfos) =>
        preTableInfos.map((tableInfo) => {
          if (tableInfo.tableName === tableName) {
            return { ...tableInfo, isActive: true };
          } else {
            return tableInfo;
          }
        })
      );
    } else {
      const tableInfo = await getTableInfo(tableName);
      setTableInfos((preTableInfos) => [...preTableInfos, tableInfo]);
    }
  }

  return (
    <div className="bg-white border border-indigo-600 shadow-md w-64 h-full float-left">
      <h2 className="text-lg font-bold p-2 bg-indigo-600 text-white">
        {t("Common.Table")}
      </h2>
      <ul className="flex-col gap-1 flex">
        {tableList.map((table, index) => (
          <li key={index} className="p-1">
            <div
              className="flex-col flex p-2 bg-white rounded-lg hover:bg-gray-200 hover:cursor-pointer"
              onClick={() => clickTableName(table)}
            >
              <div className="h-5 gap-3 flex">
                <h2 className="text-gray-800 text-base font-medium leading-snug">
                  {table}
                </h2>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
