import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  getAuthToken,
  getFilesSafe,
  getOsInfo,
} from "./api/bridge/tauri-commands";
import { getEconomiconAPI } from "./api/endpoints";
import { showMessageDialog } from "./lib/dialog/message";
import { useCurrentPageStore } from "./stores/currentView";
import { useLoadingStore } from "./stores/loading";
import { useSettingsStore } from "./stores/settings";
import { useTableListStore } from "./stores/tableList";

import {
  Panel,
  Group as PanelGroup,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { LoadingOverlay } from "./components/molecules/Loading/LoadingOverlay";
import { MessageDialog } from "./components/molecules/Modal/MessageDialog";
import { AppBar } from "./components/organisms/Header/AppBar";
import { LeftSideMenu } from "./components/pages/LeftSideMenu";
import { MainView } from "./components/pages/MainView";
import { useFilesStore } from "./stores/files";

export const App = () => {
  const { t } = useTranslation();
  const setSettings = useSettingsStore((state) => state.setSettings);
  const setOsInfo = useSettingsStore((state) => state.setOsInfo);
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
        // 認証トークンを取得する。
        // Rust 側で起動時に生成されたトークンが確認できるまで後続の
        // API リクエストをブロックする。トークン自体は Rust プロキシが
        // X-Auth-Token ヘッダーとして自動付与するため、React 側での
        // ヘッダー設定は不要。
        await getAuthToken();

        // RustからOS情報を取得（ファイルシステム認識のため最初に取得）
        const osInfo = await getOsInfo();

        if (isMounted) setOsInfo(osInfo);

        // 設定を取得
        const resGetSettings = await api.getSettings();
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
        // ファイル一覧をTauriコマンドで直接取得（Pythonサーバー非経由）
        // getFilesSafe: lastOpenedPath が消えていてもホームディレクトリへフォールバックする
        const files = await getFilesSafe(apiSettings.lastOpenedPath);
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
          setSettings(apiSettings);
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
  }, [setCurrentView, setFiles, setOsInfo, setSettings, setTableList, t]);

  return (
    <>
      <div className="flex h-screen flex-col overflow-hidden bg-white">
        <AppBar />
        <PanelGroup orientation="horizontal" className="flex-1 overflow-hidden">
          <Panel defaultSize={256} minSize={160} maxSize={480}>
            <LeftSideMenu />
          </Panel>
          <PanelResizeHandle className="w-1 cursor-col-resize bg-brand-border/50 transition-colors hover:bg-white/20 focus:outline-none" />
          <Panel className="overflow-hidden">
            <MainView />
          </Panel>
        </PanelGroup>
        <MessageDialog />
      </div>
      <LoadingOverlay isVisible={isLoading} message={loadingMessage} />
    </>
  );
};
