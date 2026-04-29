import { X } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { AnalysisResultPanel } from "@/components/pages/AnalysisResultPreview";
import { VirtualTable } from "@/components/organisms/Table/VirtualTable";

export const Table = () => {
  const { t } = useTranslation();
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );
  const removeTableInfo = useTableInfosStore((state) => state.removeTableInfo);
  const setActiveResult = useAnalysisResultsStore(
    (state) => state.setActiveResult,
  );
  const tabs = useWorkspaceTabsStore((state) => state.tabs);
  const activeTabId = useWorkspaceTabsStore((state) => state.activeTabId);
  const activateTab = useWorkspaceTabsStore((state) => state.activateTab);
  const closeTab = useWorkspaceTabsStore((state) => state.closeTab);
  const syncDataTabs = useWorkspaceTabsStore((state) => state.syncDataTabs);
  const pruneMissingDataTabs = useWorkspaceTabsStore(
    (state) => state.pruneMissingDataTabs,
  );

  useEffect(() => {
    pruneMissingDataTabs(tableInfos.map((table) => table.tableName));
  }, [pruneMissingDataTabs, tableInfos]);
  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? null;

  useEffect(() => {
    syncDataTabs(
      tableInfos.map((table) => table.tableName),
      activeTableName,
      activeTab?.kind === "result",
    );
  }, [activeTab?.kind, activeTableName, syncDataTabs, tableInfos]);

  const activeTable =
    activeTab?.kind === "data"
      ? (tableInfos.find((table) => table.tableName === activeTab.tableName) ??
        null)
      : null;

  const handleActivateTab = (tabId: string) => {
    const tab = tabs.find((item) => item.id === tabId);
    if (!tab) return;
    activateTab(tabId);
    if (tab.kind === "data") {
      activateTableInfo(tab.tableName);
      return;
    }

    setActiveResult(tab.resultId, tab.detail);
  };

  const handleCloseTab = (tabId: string) => {
    const tab = tabs.find((item) => item.id === tabId);
    if (!tab) return;

    closeTab(tabId);
    if (tab.kind === "data") {
      removeTableInfo(tab.tableName);
      return;
    }

    setActiveResult(null, null);
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* タブヘッダー */}
      <div className="border-b border-gray-200 shrink-0">
        <nav className="-mb-px flex space-x-1 overflow-x-auto">
          {tabs.map((tab) => (
            <div
              role="button"
              tabIndex={0}
              key={tab.id}
              onClick={() => handleActivateTab(tab.id)}
              className={cn(
                "group flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                tab.kind === "result" && "min-w-44 max-w-64 pr-3",
                activeTabId === tab.id
                  ? "border-brand-primary text-brand-primary"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
              )}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  handleActivateTab(tab.id);
                }
              }}
            >
              <span className="truncate">{tab.title}</span>
              <button
                type="button"
                aria-label={t("Table.CloseTab")}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseTab(tab.id);
                }}
                className={cn(
                  "rounded-full w-4 h-4 flex items-center justify-center transition-colors",
                  "opacity-0 group-hover:opacity-100 focus:opacity-100",
                  activeTabId === tab.id
                    ? "hover:bg-brand-primary/20 text-brand-primary"
                    : "hover:bg-gray-200 text-gray-400 hover:text-gray-600",
                )}
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
        </nav>
      </div>

      {/* テーブル本体: アクティブなテーブルのみマウント */}
      {tabs.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center text-brand-text-sub">
          <p className="text-sm">{t("Table.EmptyState")}</p>
        </div>
      )}
      {activeTable && (
        <div key={activeTable.tableName} className="flex-1 min-h-0">
          <VirtualTable tableInfo={activeTable} />
        </div>
      )}
      {activeTab?.kind === "result" && (
        <div key={activeTab.id} className="flex-1 min-h-0 overflow-y-auto">
          <AnalysisResultPanel detail={activeTab.detail} />
        </div>
      )}
    </div>
  );
};
