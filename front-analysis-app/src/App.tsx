import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { showErrorDialog } from './function/errorDialog';
import { getFiles, getSettings, getTableNameList } from "./function/restApis";
import useCurrentViewStore from "./stores/useCurrentViewStore";
import useSettingsStore from "./stores/useSettingsStore";
import useTableListStore from "./stores/useTableListStore";

import { ErrorDialog } from "./components/molecules/Modal/ErrorDialog";
import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/organisms/MainView/LeftSideMenu";
import { MainView } from "./components/organisms/MainView/MainView";
import useFilesStore from "./stores/useFilesStore";

export function App() {
  const { t } = useTranslation();
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setTableList = useTableListStore((state) => state.setTableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
  const setFiles = useFilesStore((state) => state.setFiles);

  useEffect(() => {
    let ignore = false;
    async function initialize() {
      try {
        const resGetSettings = await getSettings();
        if (resGetSettings.code !== "OK") {
          showErrorDialog(t('Common.Error'), resGetSettings.message);
          return;
        }
        const resGetFiles = await getFiles(resGetSettings.result.settings.defaultFolderPath);
        if (resGetFiles.code !== "OK") {
          showErrorDialog(t('Common.Error'), resGetFiles.message);
          return;
        }
        const resGetTableNames = await getTableNameList();
        if (resGetTableNames.code !== "OK") {
          showErrorDialog(t('Common.Error'), resGetTableNames.message);
          return;
        }
        if (!ignore) {
          setSettings(resGetSettings.result);
          setCurrentView({ currentView: "selectFile" });
          setTableList(resGetTableNames.result.tableNameList);
          setFiles(resGetFiles.result);
        }
      } catch (error) {
        showErrorDialog(t('Common.Error'), t('Common.UnexpectedError'));
      }
    }
    initialize();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-white">
      <HeaderMenu />
      <div
        className="flex flex-1 overflow-hidden"
      >
        <LeftSideMenu/>
        <MainView/>
      </div>
      <ErrorDialog />
    </div>
  );
}
