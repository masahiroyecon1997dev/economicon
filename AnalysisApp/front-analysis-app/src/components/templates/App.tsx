import React, { useEffect, useState } from 'react';

import { HEADER_MENU_HEIGHT } from '../../common/constant';
import { getTableNameList } from '../../functiom/restApis';
import { TableInfosType } from '../../types/stateTypes';

import { getTableInfo } from '../../functiom/internalFunctions';
import { HeaderMenu } from '../organisms/Header/HeaderMenu';
import { MainPanel } from '../organisms/MainPanel/MainPanel';

export function App() {
  const [tableInfos, setTableInfos] = useState<TableInfosType>([]);

  useEffect(() => {
    let ignore = false;
    async function initializeData() {
      const resGetTableNames = await getTableNameList();
      for (const tableName of resGetTableNames.result.tableNameList) {
        const tableInfo = await getTableInfo(tableName);
        if (!ignore) {
          console.log('aaa');
          setTableInfos(preTableInfos => [...preTableInfos, tableInfo]);
        }
      }
    }
    initializeData();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="App h-full">
      <div style={{ height: `${HEADER_MENU_HEIGHT}px` }}>
        <HeaderMenu setTableInfos={setTableInfos} />
      </div>
      <div className="flex" style={{ height: `calc(100% - ${HEADER_MENU_HEIGHT}px)` }}>
        {/* <LeftSideMenu
          tableInfos={tableInfos}
          setTableInfos={setTableInfos}
          tableList={tableList}
        ></LeftSideMenu> */}
        <MainPanel tableInfos={tableInfos}></MainPanel>
      </div>
    </div>
  );
}
