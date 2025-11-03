import { useEffect, useState } from "react";
import { getSettings, getTableNameList } from "./function/restApis";
import useSettingsStore from "./stores/useSettingsStore";
import useTableListStore from "./stores/useTableListStore";
import type { CurrentViewType } from "./types/stateTypes";

import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/organisms/MainView/LeftSideMenu";
import { MainView } from "./components/organisms/MainView/MainView";

export function App() {
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setTableList = useTableListStore((state) => state.setTableList);
  const [currentView, setCurrentView] = useState<CurrentViewType>("selectFile");

  useEffect(() => {
    let ignore = false;
    async function initialize() {
      const resGetSettings = await getSettings();
      const resGetTableNames = await getTableNameList();
      if (!ignore) {
        setSettings(resGetSettings.result);
        setTableList(resGetTableNames.result.tableNameList);
      }
    }
    initialize();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-white">
      <HeaderMenu
        setCurrentView={setCurrentView}
      />
      <div
        className="flex flex-1 overflow-hidden"
      >
        <LeftSideMenu/>
        <MainView
          currentView={currentView}
        ></MainView>
      </div>
    </div>
  );
}
