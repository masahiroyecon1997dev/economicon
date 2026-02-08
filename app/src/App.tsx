import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { getFiles, getSettings, getTableList } from "./lib/api/endpoints";
import { showMessageDialog } from './lib/dialog/message';
import { useCurrentPageStore } from "./stores/currentView";
import { useLoadingStore } from "./stores/loading";
import { useSettingsStore } from "./stores/settings";
import { useTableListStore } from "./stores/tableList";

import { LoadingOverlay } from "./components/molecules/Loading/LoadingOverlay";
import { MessageDialog } from "./components/molecules/Modal/MessageDialog";
import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/pages/LeftSideMenu";
import { MainView } from "./components/pages/MainView";
import { useFilesStore } from "./stores/files";

export const App = () => {
  const { t } = useTranslation();
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setTableList = useTableListStore((state) => state.setTableList);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
  const setFiles = useFilesStore((state) => state.setFiles);
  const { isLoading, loadingMessage } = useLoadingStore();

  useEffect(() => {
    // Strict Mode対応: 初期化が既に実行されている場合はスキップ
    // if (initialized.current) return;

    let isMounted = true;

    async function initialize() {
      try {
        // 設定を取得
        const resGetSettings = await getSettings();
        if (resGetSettings.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(t('Error.Error'), resGetSettings.message);
          }
          return;
        }
        // ファイル一覧を取得
        const resGetFiles = await getFiles(resGetSettings.result.defaultFolderPath);
        if (resGetFiles.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(t('Error.Error'), resGetFiles.message);
          }
          return;
        }
        // テーブル名一覧を取得
        const resGetTableNames = await getTableList();
        if (resGetTableNames.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(t('Error.Error'), resGetTableNames.message);
          }
          return;
        }
        // 全て成功した場合のみストアを更新
        if (isMounted) {
          setSettings(resGetSettings.result);
          setCurrentView("ImportDataFile");
          setTableList(resGetTableNames.result.tableNameList);
          setFiles(resGetFiles.result);
        }
      } catch (error) {
        console.error('App initialization error:', error);
        if (isMounted) {
          await showMessageDialog(t('Error.Error'), t('Error.UnexpectedError'));
        }
      }
    }

    initialize();

    return () => {
      isMounted = false;
    };
  }, [setCurrentView, setFiles, setSettings, setTableList, t]);

  return (
    <>
      <div className="flex h-screen flex-col overflow-hidden bg-white">
        <HeaderMenu />
        <div
          className="flex flex-1 overflow-hidden"
        >
          <LeftSideMenu />
          <MainView />
        </div>
        <MessageDialog />
      </div>
      <LoadingOverlay
        isVisible={isLoading}
        message={loadingMessage}
      />
    </>
  );
}
