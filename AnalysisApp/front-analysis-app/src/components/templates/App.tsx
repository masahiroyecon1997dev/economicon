import React, { useState, useEffect } from 'react';

import { HEADER_MENU_HEIGHT } from '../../common/constant';
import { TableInfosType, TableListType } from '../../types/stateTypes';
import { getTableNameList } from '../../functiom/restApis';

import { HeaderMenu } from '../organisms/Header/HeaderMenu';
import { LeftSideMenu } from '../organisms/MainPanel/LeftSideMenu';
import { MainPanel } from '../organisms/MainPanel/MainPanel';

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
      <div style={{ height: `${HEADER_MENU_HEIGHT}px` }}>
        <HeaderMenu setTableInfos={setTableInfos} setTableList={setTableList} />
      </div>
      <div className="flex" style={{ height: `calc(100% - ${HEADER_MENU_HEIGHT}px)` }}>
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
