import { useEffect, useState } from "react";

import { HEADER_MENU_HEIGHT } from "./common/constant";
import { getTableNameList } from "./function/restApis";
import type { TableInfosType } from "./types/stateTypes";

import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/organisms/MainPanel/LeftSideMenu";
import { getTableInfo } from "./function/internalFunctions";

export function App() {
  const [tableInfos, setTableInfos] = useState<TableInfosType>([]);

  useEffect(() => {
    let ignore = false;
    async function initializeData() {
      const resGetTableNames = await getTableNameList();
      for (const tableName of resGetTableNames.result.tableNameList) {
        const tableInfo = await getTableInfo(tableName);
        console.log(tableInfo);
        if (!ignore) {
          setTableInfos((preTableInfos) => [...preTableInfos, tableInfo]);
        }
      }
    }
    initializeData();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="App h-screen">
      <div style={{ height: `${HEADER_MENU_HEIGHT}px` }}>
        <HeaderMenu setTableInfos={setTableInfos} />
      </div>
      <div
        className="flex"
        style={{ height: `calc(100% - ${HEADER_MENU_HEIGHT}px)` }}
      >
        <LeftSideMenu
          tableInfos={tableInfos}
          setTableInfos={setTableInfos}
        ></LeftSideMenu>
        {/* <MainPanel tableInfos={tableInfos}></MainPanel> */}
      </div>
    </div>
  );
}
