import React, { useState, useEffect } from "react";

import { TableInfosType, TableListType } from "../../types/stateTypes";
import { getTableNameList } from "../../functiom/restApis";

import { HeaderMenu } from "../organisms/HeaderMenu/HeaderMenu";
import { LeftSideMenu } from "../organisms/LeftSideMenu/LeftSideMenu";
import { MainPanel } from "../organisms/MainPanel/MainPanel";

export function App() {
  const [tableInfos, setTableInfos] = useState<TableInfosType>([]);
  const [tableList, setTableList] = useState<TableListType>([]);

  useEffect(() => {
    let ignore = false;
    async function initializeData() {
      const resGetTableNames = await getTableNameList();
      if (!ignore) {
        setTableList(resGetTableNames.result.tableNameList);
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
      <div className="flex pt-0.5 pl-1">
        <LeftSideMenu
          tableInfos={tableInfos}
          setTableInfos={setTableInfos}
          tableList={tableList}
        ></LeftSideMenu>
        <MainPanel tableInfos={tableInfos}></MainPanel>
      </div>
    </div>
  );
}
