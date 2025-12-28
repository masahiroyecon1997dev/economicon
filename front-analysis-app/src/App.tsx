import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from './function/messageDialog';
import { getFiles, getSettings, getTableNameList } from "./function/restApis";
import { useCurrentViewStore } from "./stores/useCurrentViewStore";
import { useLoadingStore } from "./stores/useLoadingStore";
import { useSettingsStore } from "./stores/useSettingsStore";
import { useTableListStore } from "./stores/useTableListStore";

import { LoadingOverlay } from "./components/molecules/Loading/LoadingOverlay";
import { MessageDialog } from "./components/molecules/Modal/MessageDialog";
import { HeaderMenu } from "./components/organisms/Header/HeaderMenu";
import { LeftSideMenu } from "./components/organisms/MainView/LeftSideMenu";
import { MainView } from "./components/organisms/MainView/MainView";
import { useFilesStore } from "./stores/useFilesStore";

export const App = () => {
  const { t } = useTranslation();
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setTableList = useTableListStore((state) => state.setTableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
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
        const resGetTableNames = await getTableNameList();
        if (resGetTableNames.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(t('Error.Error'), resGetTableNames.message);
          }
          return;
        }
        // 全て成功した場合のみストアを更新
        if (isMounted) {
          setSettings(resGetSettings.result);
          setCurrentView("SelectFile");
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
  }, []);

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
