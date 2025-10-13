import { useEffect, useState } from "react";

import { getTableNameList } from "./function/restApis";
import type { TableInfosType, TableNameListType } from "./types/stateTypes";

import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/organisms/MainPanel/LeftSideMenu";
import { MainPanel } from "./components/organisms/MainPanel/MainPanel";

export function App() {
  const [tableNameList, setTableNameList] = useState<TableNameListType>([]);
  const [tableInfos, setTableInfos] = useState<TableInfosType>([]);

  useEffect(() => {
    let ignore = false;
    async function initializeData() {
      const resGetTableNames = await getTableNameList();
      if (!ignore) {
        setTableNameList(resGetTableNames.result.tableNameList);
      }
    }
    initializeData();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-white">
      <HeaderMenu setTableNameList={setTableNameList} setTableInfos={setTableInfos} />
      <div
        className="flex flex-1 overflow-hidden"
      >
        <LeftSideMenu
          tableNameList={tableNameList}
          tableInfos={tableInfos}
          setTableInfos={setTableInfos}
        ></LeftSideMenu>
        <MainPanel tableInfos={tableInfos}></MainPanel>
      </div>
    </div>
  );
}
