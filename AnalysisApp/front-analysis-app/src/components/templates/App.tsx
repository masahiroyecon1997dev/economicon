import React, { useState, useEffect } from "react";

import { TableInfosType } from "../../types/stateTypes";
import { fetchData } from "../../functiom/internalFunctions";
import { getTableNameList, getColumnNameList } from "../../functiom/restApis";

import { HeaderMenu } from "../organisms/HeaderMenu/HeaderMenu";
import { MainTable } from "../organisms/MainTable/MainTable";

export function App() {
  const [tableInfos, setTableInfos] = useState<TableInfosType>([]);

  useEffect(() => {
    let ignore = false;
    async function initializeData() {
      const resGetTableNames = await getTableNameList();
      if (!ignore) {
        if (resGetTableNames.result.tableNameList.length > 0) {
          for (const tableName of resGetTableNames.result.tableNameList) {
            const data = await fetchData(tableName);
            const columnList = await getColumnNameList(tableName);
            setTableInfos((preTableInfos) => [
              ...preTableInfos,
              {
                tableName: data.tableName,
                columnNameList: columnList.result.columnNameList,
                data: data.data,
              },
            ]);
          }
        }
      }
    }
    initializeData();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="App">
      <HeaderMenu setTableInfos={setTableInfos} />
      <div className="p-4">
        <h1 className="text-2xl font-bold">Excel-like Header Menu</h1>
        {tableInfos[0]?.tableName ? (
          <MainTable tableInfo={tableInfos[0]}></MainTable>
        ) : (
          <></>
        )}
      </div>
    </div>
  );
}
