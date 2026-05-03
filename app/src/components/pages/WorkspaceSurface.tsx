import type { AnalysisResultDetail } from "@/api/model";
import { EditAnalysisResultDialog } from "@/components/organisms/Dialog/EditAnalysisResultDialog";
import { VirtualTable } from "@/components/organisms/Table/VirtualTable";
import { AnalysisResultPanel } from "@/components/pages/AnalysisResultPreview";
import { Calculation } from "@/components/pages/Calculation";
import { CorrelationMatrix } from "@/components/pages/CorrelationMatrix";
import { ConfidenceIntervalView } from "@/components/pages/ConfidenceIntervalView";
import { CreateSimulationDataTable } from "@/components/pages/CreateSimulationDataTable";
import { JoinTable } from "@/components/pages/JoinTable";
import { Regression } from "@/components/pages/RegressionView";
import { UnionTable } from "@/components/pages/UnionTable";
import { isWorkFeatureKey } from "@/constants/workspaceTabs";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import type {
  WorkFeatureKey,
  WorkspaceTab,
  WorkspaceWorkTab,
} from "@/stores/workspaceTabs";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

type StaticWorkFeatureKey = Exclude<WorkFeatureKey, "CorrelationMatrix">;

const WORK_TAB_COMPONENTS: Record<StaticWorkFeatureKey, React.ReactElement> = {
  JoinTable: <JoinTable />,
  UnionTable: <UnionTable />,
  CreateSimulationDataTable: <CreateSimulationDataTable />,
  CalculationView: <Calculation />,
  ConfidenceIntervalView: <ConfidenceIntervalView />,
  LinearRegressionForm: <Regression />,
};

const findLastNonWorkTab = (tabs: WorkspaceTab[], excludedId: string) => {
  for (let index = tabs.length - 1; index >= 0; index -= 1) {
    const tab = tabs[index];
    if (tab.id !== excludedId && tab.kind !== "work") {
      return tab;
    }
  }
  return null;
};

export const WorkspaceSurface = () => {
  const { t } = useTranslation();
  const currentView = useCurrentPageStore((state) => state.currentView);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
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
  const openDataTab = useWorkspaceTabsStore((state) => state.openDataTab);
  const syncDataTabs = useWorkspaceTabsStore((state) => state.syncDataTabs);
  const pruneMissingDataTabs = useWorkspaceTabsStore(
    (state) => state.pruneMissingDataTabs,
  );
  const setWorkTabDirty = useWorkspaceTabsStore(
    (state) => state.setWorkTabDirty,
  );

  const [editTarget, setEditTarget] = useState<AnalysisResultDetail | null>(
    null,
  );
  const previousViewRef = useRef(currentView);
  const workTabContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    pruneMissingDataTabs(tableInfos.map((table) => table.tableName));
  }, [pruneMissingDataTabs, tableInfos]);

  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? null;

  useEffect(() => {
    syncDataTabs(
      tableInfos.map((table) => table.tableName),
      activeTableName,
      activeTab?.kind !== "data",
    );
  }, [activeTab?.kind, activeTableName, syncDataTabs, tableInfos]);

  useEffect(() => {
    const previousView = previousViewRef.current;
    previousViewRef.current = currentView;

    if (
      activeTab?.kind !== "work" ||
      currentView !== "DataPreview" ||
      !isWorkFeatureKey(previousView)
    ) {
      return;
    }

    const fallbackTab = findLastNonWorkTab(tabs, activeTab.id);
    if (fallbackTab) {
      activateTab(fallbackTab.id);
      if (fallbackTab.kind === "data") {
        activateTableInfo(fallbackTab.tableName);
      } else {
        setActiveResult(fallbackTab.resultId, fallbackTab.detail);
      }
      return;
    }

    closeTab(activeTab.id);
  }, [
    activateTab,
    activateTableInfo,
    activeTab,
    closeTab,
    currentView,
    setActiveResult,
    tabs,
  ]);

  useEffect(() => {
    if (activeTab?.kind !== "work") return;
    const container = workTabContainerRef.current;
    if (!container) return;

    const markDirty = () => {
      if (!activeTab.dirty) {
        setWorkTabDirty(activeTab.id, true);
      }
    };

    container.addEventListener("input", markDirty, true);
    container.addEventListener("change", markDirty, true);

    return () => {
      container.removeEventListener("input", markDirty, true);
      container.removeEventListener("change", markDirty, true);
    };
  }, [activeTab, setWorkTabDirty]);

  const activeTable =
    activeTab?.kind === "data"
      ? (tableInfos.find((table) => table.tableName === activeTab.tableName) ??
        null)
      : null;

  const activateWorkspaceTab = (tab: WorkspaceTab) => {
    activateTab(tab.id);
    if (tab.kind === "data") {
      activateTableInfo(tab.tableName);
      setCurrentView("DataPreview");
      return;
    }
    if (tab.kind === "result") {
      setActiveResult(tab.resultId, tab.detail);
      setCurrentView("DataPreview");
      return;
    }
    setCurrentView(tab.featureKey);
  };

  const handleActivateTab = (tabId: string) => {
    const tab = tabs.find((item) => item.id === tabId);
    if (!tab) return;
    activateWorkspaceTab(tab);
  };

  const handleCloseTab = async (tabId: string) => {
    const tab = tabs.find((item) => item.id === tabId);
    if (!tab) return;

    if (tab.kind === "work" && tab.dirty) {
      const confirmed = await showConfirmDialog(
        t("WorkspaceSurface.CloseDirtyWorkTabTitle"),
        t("WorkspaceSurface.CloseDirtyWorkTabMessage"),
      );
      if (!confirmed) return;
    }

    closeTab(tabId);
    if (tab.kind === "data") {
      removeTableInfo(tab.tableName);
      return;
    }
    if (tab.kind === "result") {
      setActiveResult(null, null);
      return;
    }
    if (activeTabId === tabId) {
      setCurrentView("DataPreview");
    }
  };

  const renderWorkTab = (tab: WorkspaceWorkTab) => {
    if (tab.featureKey === "CorrelationMatrix") {
      return (
        <CorrelationMatrix
          workTabId={tab.id}
          onSuccess={(tableName) => {
            openDataTab(tableName);
            setCurrentView("DataPreview");
          }}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    return WORK_TAB_COMPONENTS[tab.featureKey];
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="border-b border-gray-200 shrink-0">
        <nav className="app-scrollbar -mb-px flex space-x-1 overflow-x-auto">
          {tabs.map((tab) => (
            <div
              role="button"
              tabIndex={0}
              key={tab.id}
              onClick={() => void handleActivateTab(tab.id)}
              className={cn(
                "group flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
                tab.kind === "result" && "min-w-44 max-w-64 pr-3",
                activeTabId === tab.id
                  ? "border-brand-primary text-brand-primary"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
              )}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  void handleActivateTab(tab.id);
                }
              }}
            >
              <span className="truncate">{tab.title}</span>
              {tab.kind === "work" && tab.dirty && (
                <span
                  className="h-2 w-2 rounded-full bg-amber-500 shrink-0"
                  aria-label={t("WorkspaceSurface.DirtyBadge")}
                />
              )}
              <button
                type="button"
                aria-label={t("Table.CloseTab")}
                onClick={(event) => {
                  event.stopPropagation();
                  void handleCloseTab(tab.id);
                }}
                className={cn(
                  "rounded-full w-4 h-4 flex items-center justify-center transition-colors shrink-0",
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
        <div
          key={activeTab.id}
          className="app-scrollbar flex-1 min-h-0 overflow-y-auto px-1 pt-1"
        >
          <AnalysisResultPanel
            detail={activeTab.detail}
            onEdit={() => setEditTarget(activeTab.detail)}
          />
        </div>
      )}
      {activeTab?.kind === "work" && (
        <div
          ref={workTabContainerRef}
          key={activeTab.id}
          className="app-scrollbar flex-1 min-h-0 overflow-y-auto"
          data-testid={`workspace-work-tab-${activeTab.featureKey}`}
        >
          {renderWorkTab(activeTab)}
        </div>
      )}

      {editTarget && (
        <EditAnalysisResultDialog
          isOpen={!!editTarget}
          detail={editTarget}
          onClose={() => setEditTarget(null)}
        />
      )}
    </div>
  );
};