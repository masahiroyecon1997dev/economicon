import type { AnalysisResultDetail } from "@/api/model";
import { EditAnalysisResultDialog } from "@/components/organisms/Dialog/EditAnalysisResultDialog";
import { FERegressionForm } from "@/components/organisms/Form/FERegressionForm";
import { IVRegressionForm } from "@/components/organisms/Form/IVRegressionForm";
import { LinearRegressionForm } from "@/components/organisms/Form/LinearRegressionForm";
import { LogitRegressionForm } from "@/components/organisms/Form/LogitRegressionForm";
import { ProbitRegressionForm } from "@/components/organisms/Form/ProbitRegressionForm";
import { RERegressionForm } from "@/components/organisms/Form/RERegressionForm";
import { WLSRegressionForm } from "@/components/organisms/Form/WLSRegressionForm";
import { VirtualTable } from "@/components/organisms/Table/VirtualTable";
import { AnalysisResultPanel } from "@/components/pages/AnalysisResultPreview";
import { AsymptoticNormality } from "@/components/pages/AsymptoticNormality";
import { Calculation } from "@/components/pages/Calculation";
import { ConfidenceIntervalSim } from "@/components/pages/ConfidenceIntervalSim";
import { ConfidenceIntervalView } from "@/components/pages/ConfidenceIntervalView";
import { Consistency } from "@/components/pages/Consistency";
import { CorrelationMatrix } from "@/components/pages/CorrelationMatrix";
import { CreateSimulationDataTable } from "@/components/pages/CreateSimulationDataTable";
import { DescriptiveStatistics } from "@/components/pages/DescriptiveStatistics";
import { DistributionPreview } from "@/components/pages/DistributionPreview";
import { GroupStatistics } from "@/components/pages/GroupStatistics";
import { JoinTable } from "@/components/pages/JoinTable";
import { PlotView } from "@/components/pages/PlotView";
import { StatisticalTestView } from "@/components/pages/StatisticalTestView";
import { Unbiasedness } from "@/components/pages/Unbiasedness";
import { UnionTable } from "@/components/pages/UnionTable";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { cn } from "@/lib/utils/helpers";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useTableInfosStore } from "@/stores/tableInfos";
import type {
  WorkFeatureKey,
  WorkspaceTab,
  WorkspaceWorkTab,
} from "@/stores/workspaceTabs";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { X } from "lucide-react";
import {
  Fragment,
  useEffect,
  useRef,
  useState,
  type PointerEvent,
} from "react";
import { useTranslation } from "react-i18next";

type TabDropTarget = {
  index: number;
};

type StaticWorkFeatureKey = Exclude<
  WorkFeatureKey,
  | "CorrelationMatrix"
  | "DescriptiveStatistics"
  | "StatisticalTestView"
  | "LinearRegressionForm"
  | "WLSRegressionForm"
  | "LogitRegressionForm"
  | "ProbitRegressionForm"
  | "IVRegressionForm"
  | "FERegressionForm"
  | "RERegressionForm"
  | "GroupStatistics"
  | "PlotView"
>;

const WORK_TAB_COMPONENTS: Record<StaticWorkFeatureKey, React.ReactElement> = {
  JoinTable: <JoinTable />,
  UnionTable: <UnionTable />,
  CreateSimulationDataTable: <CreateSimulationDataTable />,
  CalculationView: <Calculation />,
  ConfidenceIntervalView: <ConfidenceIntervalView />,
  DistributionPreview: <DistributionPreview />,
  ConfidenceIntervalSim: <ConfidenceIntervalSim />,
  AsymptoticNormality: <AsymptoticNormality />,
  Consistency: <Consistency />,
  Unbiasedness: <Unbiasedness />,
};

const isCorrelationMatrixWorkTab = (
  tab: WorkspaceWorkTab,
): tab is WorkspaceWorkTab & {
  featureKey: "CorrelationMatrix";
  id: "work:CorrelationMatrix";
} => tab.featureKey === "CorrelationMatrix";

const isStatisticalTestWorkTab = (
  tab: WorkspaceWorkTab,
): tab is WorkspaceWorkTab & {
  featureKey: "StatisticalTestView";
  id: "work:StatisticalTestView";
} => tab.featureKey === "StatisticalTestView";

const isDescriptiveStatisticsWorkTab = (
  tab: WorkspaceWorkTab,
): tab is WorkspaceWorkTab & {
  featureKey: "DescriptiveStatistics";
  id: "work:DescriptiveStatistics";
} => tab.featureKey === "DescriptiveStatistics";

const isGroupStatisticsWorkTab = (
  tab: WorkspaceWorkTab,
): tab is WorkspaceWorkTab & {
  featureKey: "GroupStatistics";
  id: "work:GroupStatistics";
} => tab.featureKey === "GroupStatistics";

const isPlotViewWorkTab = (
  tab: WorkspaceWorkTab,
): tab is WorkspaceWorkTab & {
  featureKey: "PlotView";
  id: "work:PlotView";
} => tab.featureKey === "PlotView";

export const WorkspaceSurface = () => {
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
  const moveTab = useWorkspaceTabsStore((state) => state.moveTab);
  const openDataTab = useWorkspaceTabsStore((state) => state.openDataTab);
  const closeActiveWorkTab = useWorkspaceTabsStore(
    (state) => state.closeActiveWorkTab,
  );
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
  const [draggedTabId, setDraggedTabId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<TabDropTarget | null>(null);
  const workTabContainerRef = useRef<HTMLDivElement | null>(null);
  const pointerDragRef = useRef<{
    tabId: string;
    pointerId: number;
    startX: number;
    dragging: boolean;
  } | null>(null);
  const tabNodeRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const skipNextClickRef = useRef(false);

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
      return;
    }
    if (tab.kind === "result") {
      setActiveResult(tab.resultId, tab.detail);
      return;
    }
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
  };

  const handleMoveTabByKeyboard = (tabId: string, direction: -1 | 1) => {
    const currentIndex = tabs.findIndex((tab) => tab.id === tabId);
    if (currentIndex === -1) return;

    const targetIndex = Math.max(
      0,
      Math.min(currentIndex + direction, tabs.length - 1),
    );

    if (targetIndex === currentIndex) return;

    moveTab(tabId, direction === 1 ? targetIndex + 1 : targetIndex);
  };

  const resetDragState = () => {
    setDraggedTabId(null);
    setDropTarget(null);
  };

  const DRAG_THRESHOLD_PX = 4;

  const resolveDropIndexFromPointer = (clientX: number): number => {
    for (let i = 0; i < tabs.length; i++) {
      const el = tabNodeRefs.current.get(tabs[i].id);
      if (!el) continue;
      const { left, width } = el.getBoundingClientRect();
      if (clientX < left + width / 2) return i;
    }
    return tabs.length;
  };

  const handleTabPointerDown = (
    event: PointerEvent<HTMLDivElement>,
    tabId: string,
  ) => {
    if (event.button !== 0) return;
    if ((event.target as HTMLElement).closest("button")) return;
    pointerDragRef.current = {
      tabId,
      pointerId: event.pointerId,
      startX: event.clientX,
      dragging: false,
    };
  };

  const handleTabPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    const state = pointerDragRef.current;
    if (!state) return;
    if (!state.dragging) {
      if (Math.abs(event.clientX - state.startX) < DRAG_THRESHOLD_PX) return;
      state.dragging = true;
      event.currentTarget.setPointerCapture(state.pointerId);
      setDraggedTabId(state.tabId);
    }
    setDropTarget({ index: resolveDropIndexFromPointer(event.clientX) });
  };

  const handleTabPointerUp = (event: PointerEvent<HTMLDivElement>) => {
    const state = pointerDragRef.current;
    if (!state) return;
    if (state.dragging) {
      event.currentTarget.releasePointerCapture(state.pointerId);
      moveTab(state.tabId, resolveDropIndexFromPointer(event.clientX));
      skipNextClickRef.current = true;
    }
    pointerDragRef.current = null;
    resetDragState();
  };

  const handleTabPointerCancel = (event: PointerEvent<HTMLDivElement>) => {
    const state = pointerDragRef.current;
    if (!state) return;
    if (state.dragging) {
      event.currentTarget.releasePointerCapture(state.pointerId);
    }
    pointerDragRef.current = null;
    resetDragState();
  };

  const renderWorkTab = (tab: WorkspaceWorkTab) => {
    if (tab.featureKey === "FERegressionForm") {
      return <FERegressionForm onCancel={() => void handleCloseTab(tab.id)} />;
    }
    if (tab.featureKey === "RERegressionForm") {
      return <RERegressionForm onCancel={() => void handleCloseTab(tab.id)} />;
    }

    if (isCorrelationMatrixWorkTab(tab)) {
      return (
        <CorrelationMatrix
          workTabId={tab.id}
          onSuccess={(tableName) => {
            closeActiveWorkTab();
            openDataTab(tableName);
          }}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    if (isStatisticalTestWorkTab(tab)) {
      return (
        <StatisticalTestView
          workTabId={tab.id}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    if (isDescriptiveStatisticsWorkTab(tab)) {
      return (
        <DescriptiveStatistics
          workTabId={tab.id}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    if (isGroupStatisticsWorkTab(tab)) {
      return (
        <GroupStatistics
          workTabId={tab.id}
          onSuccess={(tableName) => {
            closeActiveWorkTab();
            openDataTab(tableName);
          }}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    if (isPlotViewWorkTab(tab)) {
      return (
        <PlotView
          workTabId={tab.id}
          onCancel={() => void handleCloseTab(tab.id)}
        />
      );
    }

    if (tab.featureKey === "LinearRegressionForm") {
      return (
        <LinearRegressionForm onCancel={() => void handleCloseTab(tab.id)} />
      );
    }

    if (tab.featureKey === "WLSRegressionForm") {
      return <WLSRegressionForm onCancel={() => void handleCloseTab(tab.id)} />;
    }

    if (tab.featureKey === "LogitRegressionForm") {
      return (
        <LogitRegressionForm onCancel={() => void handleCloseTab(tab.id)} />
      );
    }

    if (tab.featureKey === "ProbitRegressionForm") {
      return (
        <ProbitRegressionForm onCancel={() => void handleCloseTab(tab.id)} />
      );
    }

    if (tab.featureKey === "IVRegressionForm") {
      return <IVRegressionForm onCancel={() => void handleCloseTab(tab.id)} />;
    }

    const staticFeatureKey = tab.featureKey as StaticWorkFeatureKey;
    return WORK_TAB_COMPONENTS[staticFeatureKey];
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="border-b border-gray-200 dark:border-gray-700 shrink-0">
        <nav className="app-scrollbar -mb-px flex space-x-1 overflow-x-auto">
          {tabs.map((tab, index) => (
            <Fragment key={tab.id}>
              <div
                data-testid={`workspace-tab-drop-slot-${index}`}
                aria-hidden="true"
                className={cn(
                  "shrink-0 self-stretch transition-all",
                  draggedTabId ? "w-2" : "w-0",
                )}
              >
                <div
                  className={cn(
                    "h-full w-0.5 rounded-full transition-opacity",
                    dropTarget?.index === index && draggedTabId
                      ? "bg-brand-primary opacity-100"
                      : "opacity-0",
                  )}
                />
              </div>
              <div
                role="button"
                tabIndex={0}
                ref={(el) => {
                  if (el) tabNodeRefs.current.set(tab.id, el);
                  else tabNodeRefs.current.delete(tab.id);
                }}
                onPointerDown={(event) => handleTabPointerDown(event, tab.id)}
                onPointerMove={handleTabPointerMove}
                onPointerUp={handleTabPointerUp}
                onPointerCancel={handleTabPointerCancel}
                onClick={() => {
                  if (skipNextClickRef.current) {
                    skipNextClickRef.current = false;
                    return;
                  }
                  void handleActivateTab(tab.id);
                }}
                className={cn(
                  "group flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors select-none touch-none",
                  tab.kind === "result" && "min-w-44 max-w-64 pr-3",
                  activeTabId === tab.id
                    ? "border-brand-primary text-brand-primary dark:border-brand-accent dark:text-brand-accent"
                    : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:border-gray-300 dark:hover:border-gray-600",
                  draggedTabId === tab.id
                    ? "opacity-60 cursor-grabbing"
                    : "cursor-grab",
                )}
                onKeyDown={(event) => {
                  if (
                    event.altKey &&
                    event.shiftKey &&
                    event.key === "ArrowLeft"
                  ) {
                    event.preventDefault();
                    handleMoveTabByKeyboard(tab.id, -1);
                    return;
                  }

                  if (
                    event.altKey &&
                    event.shiftKey &&
                    event.key === "ArrowRight"
                  ) {
                    event.preventDefault();
                    handleMoveTabByKeyboard(tab.id, 1);
                    return;
                  }

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
                      ? "hover:bg-brand-primary/20 dark:hover:bg-brand-accent/20 text-brand-primary dark:text-brand-accent"
                      : "hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300",
                  )}
                >
                  <X className="w-2.5 h-2.5" />
                </button>
              </div>
            </Fragment>
          ))}
          <div
            data-testid={`workspace-tab-drop-slot-${tabs.length}`}
            aria-hidden="true"
            className={cn(
              "shrink-0 self-stretch transition-all",
              draggedTabId ? "w-2" : "w-0",
            )}
          >
            <div
              className={cn(
                "h-full w-0.5 rounded-full transition-opacity",
                dropTarget?.index === tabs.length && draggedTabId
                  ? "bg-brand-primary opacity-100"
                  : "opacity-0",
              )}
            />
          </div>
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
      {tabs
        .filter((t) => t.kind === "work")
        .map((tab) => {
          const workTab = tab as WorkspaceWorkTab;
          const isActive = activeTab?.id === tab.id;
          return (
            <div
              key={tab.id}
              ref={isActive ? workTabContainerRef : null}
              className={cn(
                "app-scrollbar flex-1 min-h-0 overflow-y-auto",
                !isActive && "hidden",
              )}
              data-testid={
                isActive
                  ? `workspace-work-tab-${workTab.featureKey}`
                  : undefined
              }
            >
              {renderWorkTab(workTab)}
            </div>
          );
        })}

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
