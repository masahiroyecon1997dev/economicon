import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAPI } from "./api/endpoints";
import { getFiles } from "./lib/api/endpoints";
import { showMessageDialog } from "./lib/dialog/message";
import { useCurrentPageStore } from "./stores/currentView";
import { useLoadingStore } from "./stores/loading";
import { useSettingsStore } from "./stores/settings";
import { useTableListStore } from "./stores/tableList";
import type { SettingsType } from "./types/commonTypes";

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

    const initialize = async () => {
      const api = getEconomiconAPI();
      try {
        // 設定を取得
        const resGetSettings = await api.getSettings();
        console.log("GetSettings response:", resGetSettings);
        if (resGetSettings.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(
              t("Error.Error"),
              t("Error.UnexpectedError"),
            );
          }
          return;
        }
        // GetSettingsResultをアプリのSettingsType形式にマッピング
        const apiSettings = resGetSettings.result;
        const settings: SettingsType = {
          osName: apiSettings.osName,
          defaultFolderPath: apiSettings.lastOpenedPath,
          displayRows: 100,
          appLanguage: apiSettings.language,
          encoding: apiSettings.encoding,
          pathSeparator: apiSettings.osName === "Windows" ? "\\" : "/",
        };
        // ファイル一覧をTauriコマンドで直接取得（Pythonサーバー非経由）
        const files = await getFiles(settings.defaultFolderPath);
        // テーブル名一覧を取得
        const resGetTableNames = await api.getTableList();
        if (resGetTableNames.code !== "OK") {
          if (isMounted) {
            await showMessageDialog(
              t("Error.Error"),
              t("Error.UnexpectedError"),
            );
          }
          return;
        }
        // 全て成功した場合のみストアを更新
        if (isMounted) {
          setSettings(settings);
          setCurrentView("ImportDataFile");
          setTableList(resGetTableNames.result.tableNameList);
          setFiles(files);
        }
      } catch (error) {
        console.error("App initialization error:", error);
        if (isMounted) {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      }
    };

    initialize();

    return () => {
      isMounted = false;
    };
  }, [setCurrentView, setFiles, setSettings, setTableList, t]);

  return (
    <>
      <div className="flex h-screen flex-col overflow-hidden bg-white">
        <HeaderMenu />
        <div className="flex flex-1 overflow-hidden">
          <LeftSideMenu />
          <MainView />
        </div>
        <MessageDialog />
      </div>
      <LoadingOverlay isVisible={isLoading} message={loadingMessage} />
    </>
  );
};
