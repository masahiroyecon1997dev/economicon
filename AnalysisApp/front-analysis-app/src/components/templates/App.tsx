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
    <div className="App h-full">
      <div className={`h-[40px]`}>
        <HeaderMenu setTableInfos={setTableInfos} setTableList={setTableList} />
      </div>
      <div className={`flex h-[calc(100%-40px)]`}>
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
