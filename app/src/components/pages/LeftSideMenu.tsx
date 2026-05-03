import { getEconomiconAppAPI } from "@/api/endpoints";
import type { AnalysisResultDetail } from "@/api/model";
import { SectionHeading } from "@/components/atoms/List/SectionHeading";
import { TableNav } from "@/components/molecules/List/TableNav";
import { OutputResultDialog } from "@/components/organisms/Dialog/OutputResultDialog";
import { showConfirmDialog } from "@/lib/dialog/confirm";
import { showMessageDialog } from "@/lib/dialog/message";
import { extractApiErrorMessage } from "@/lib/utils/apiError";
import { cn } from "@/lib/utils/helpers";
import { getTableInfo } from "@/lib/utils/internal";
import { useAnalysisResultsStore } from "@/stores/analysisResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import { ExternalLink, FileDown, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

const RESULT_TYPE_ORDER = [
  "descriptive_statistics",
  "confidence_interval",
  "regression",
  "statistical_test",
  "did",
  "rdd",
  "heckman",
] as const;

const OUTPUT_SUPPORTED_TYPES = new Set([
  "descriptive_statistics",
  "confidence_interval",
  "regression",
]);

type OutputSupportedType =
  | "descriptive_statistics"
  | "confidence_interval"
  | "regression";

type OutputTarget =
  | {
      id: string;
      type: "descriptive_statistics" | "confidence_interval";
      title: string;
    }
  | {
      id: string;
      type: "regression";
      title: string;
      regressionResult: LinearRegressionResultType;
    }
  | null;

export const LeftSideMenu = () => {
  const { t } = useTranslation();
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
  const tableList = useTableListStore((state) => state.tableList);
  const pane = useAnalysisResultsStore((state) => state.pane);
  const setPane = useAnalysisResultsStore((state) => state.setPane);
  const summaries = useAnalysisResultsStore((state) => state.summaries);
  const isListLoading = useAnalysisResultsStore((state) => state.isListLoading);
  const setActiveResult = useAnalysisResultsStore(
    (state) => state.setActiveResult,
  );
  const fetchSummaries = useAnalysisResultsStore(
    (state) => state.fetchSummaries,
  );
  const openResult = useAnalysisResultsStore((state) => state.openResult);
  const removeSummary = useAnalysisResultsStore((state) => state.removeSummary);
  const tabs = useWorkspaceTabsStore((state) => state.tabs);
  const activeTabId = useWorkspaceTabsStore((state) => state.activeTabId);
  const openDataTab = useWorkspaceTabsStore((state) => state.openDataTab);
  const openResultTab = useWorkspaceTabsStore((state) => state.openResultTab);
  const activateTab = useWorkspaceTabsStore((state) => state.activateTab);
  const removeResultTab = useWorkspaceTabsStore(
    (state) => state.removeResultTab,
  );
  const [outputTarget, setOutputTarget] = useState<OutputTarget>(null);

  useEffect(() => {
    if (pane !== "results") return;

    void (async () => {
      try {
        await fetchSummaries();
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          extractApiErrorMessage(error, t("Error.UnexpectedError")),
        );
      }
    })();
  }, [fetchSummaries, pane, t]);

  const groupedResults = useMemo(() => {
    const groups = new Map<string, typeof summaries>();
    const sorted = [...summaries].sort((left, right) => {
      const leftIndex = RESULT_TYPE_ORDER.indexOf(left.resultType as never);
      const rightIndex = RESULT_TYPE_ORDER.indexOf(right.resultType as never);
      const groupDelta =
        (leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex) -
        (rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex);

      if (groupDelta !== 0) return groupDelta;
      return (
        new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime()
      );
    });

    for (const summary of sorted) {
      const key = summary.resultType;
      const prev = groups.get(key) ?? [];
      groups.set(key, [...prev, summary]);
    }

    return Array.from(groups.entries()).map(([resultType, results]) => ({
      resultType,
      label: results[0]?.resultTypeLabel ?? resultType,
      results,
    }));
  }, [summaries]);

  const clickTableName = async (tableName: string) => {
    try {
      const sameTableNameInfos = tableInfos.filter(
        (tableInfo) => tableInfo.tableName === tableName,
      );
      if (sameTableNameInfos.length > 0) {
        activateTableInfo(tableName);
      } else {
        const tableInfo = await getTableInfo(tableName);
        addTableInfo(tableInfo);
      }
      openDataTab(tableName);
      setCurrentView("DataPreview");
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  const handleOpenResult = async (resultId: string) => {
    const existingTab = tabs.find((tab) => tab.id === `result:${resultId}`);
    if (existingTab?.kind === "result") {
      activateTab(existingTab.id);
      setActiveResult(existingTab.resultId, existingTab.detail);
      setCurrentView("DataPreview");
      return;
    }

    try {
      const detail = await openResult(resultId);
      openResultTab(detail);
      setCurrentView("DataPreview");
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  const handleDeleteResult = async (resultId: string, resultName: string) => {
    const confirmed = await showConfirmDialog(
      t("LeftSideMenu.DeleteResultConfirmTitle"),
      t("LeftSideMenu.DeleteResultConfirmMessage", { resultName }),
    );
    if (!confirmed) return;

    try {
      await getEconomiconAppAPI().deleteAnalysisResult(resultId);
      removeSummary(resultId);
      removeResultTab(resultId);
      if (activeTabId === `result:${resultId}`) {
        setActiveResult(null, null);
        setCurrentView(tableList.length > 0 ? "DataPreview" : "ImportDataFile");
      }
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  const formatCreatedAt = (createdAt: string) => {
    const date = new Date(createdAt);
    if (Number.isNaN(date.getTime())) return createdAt;
    return date.toLocaleString();
  };

  const toRegressionResult = (detail: AnalysisResultDetail) => {
    return {
      ...(detail.resultData as unknown as LinearRegressionResultType),
      resultId: detail.id,
    };
  };

  const handleOutputResult = async (
    id: string,
    type: OutputSupportedType,
    title: string,
  ) => {
    if (type !== "regression") {
      setOutputTarget({ id, type, title });
      return;
    }

    try {
      const response = await getEconomiconAppAPI().getAnalysisResult(id);
      setOutputTarget({
        id,
        type,
        title,
        regressionResult: toRegressionResult(response.result),
      });
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-brand-primary text-white dark:bg-gray-900">
      <SectionHeading title={t("LeftSideMenu.Title")} />
      <div
        className="px-4 pb-2 pt-1.5"
        data-testid="workspace-navigator-toggle"
      >
        <div className="grid grid-cols-2 rounded-lg bg-white/10 p-0.5">
          <button
            type="button"
            className={cn(
              "rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
              pane === "data"
                ? "bg-white text-brand-primary"
                : "text-white/70 hover:text-white",
            )}
            onClick={() => setPane("data")}
            data-testid="left-menu-tab-data"
          >
            {t("LeftSideMenu.DataTab")}
          </button>
          <button
            type="button"
            className={cn(
              "rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors",
              pane === "results"
                ? "bg-white text-brand-primary"
                : "text-white/70 hover:text-white",
            )}
            onClick={() => setPane("results")}
            data-testid="left-menu-tab-results"
          >
            {t("LeftSideMenu.ResultsTab")}
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {pane === "data" && (
          <>
            {tableList.length === 0 && (
              <p className="mt-2 whitespace-pre-line text-xs leading-relaxed text-white/40">
                {t("LeftSideMenu.EmptyState")}
              </p>
            )}
            <TableNav
              activeTableName={activeTableName}
              onTableClick={clickTableName}
            />
          </>
        )}

        {pane === "results" && (
          <div className="space-y-4" data-testid="analysis-results-list">
            {isListLoading && (
              <p className="mt-2 text-xs leading-relaxed text-white/60">
                {t("LeftSideMenu.ResultsLoading")}
              </p>
            )}

            {!isListLoading && groupedResults.length === 0 && (
              <p className="mt-2 whitespace-pre-line text-xs leading-relaxed text-white/40">
                {t("LeftSideMenu.ResultsEmptyState")}
              </p>
            )}

            {!isListLoading &&
              groupedResults.map((group) => (
                <section key={group.resultType} className="space-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-white/60">
                    {group.label}
                  </h3>
                  <div className="space-y-2">
                    {group.results.map((result) => {
                      const supportsOutput = OUTPUT_SUPPORTED_TYPES.has(
                        result.resultType,
                      );
                      return (
                        <div
                          key={result.id}
                          className={cn(
                            "rounded-lg border border-white/10 bg-white/5 p-2 transition-colors",
                            activeTabId === `result:${result.id}` &&
                              "border-brand-accent bg-white/10",
                          )}
                          data-testid={`analysis-result-item-${result.id}`}
                        >
                          <div className="flex items-start gap-2">
                            <button
                              type="button"
                              className="flex min-w-0 flex-1 flex-col items-start text-left"
                              onClick={() => void handleOpenResult(result.id)}
                              data-testid={`analysis-result-open-${result.id}`}
                            >
                              <div className="flex w-full items-center gap-2">
                                <span className="rounded bg-white/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white/80">
                                  {result.resultTypeLabel}
                                </span>
                                <span className="truncate text-sm font-medium text-white">
                                  {result.name}
                                </span>
                              </div>
                              <span className="mt-1 truncate text-xs text-white/70">
                                {result.tableName}
                              </span>
                              <span className="mt-0.5 truncate text-xs text-white/50">
                                {result.summaryText ||
                                  formatCreatedAt(result.createdAt)}
                              </span>
                            </button>

                            <div className="flex shrink-0 items-center gap-1">
                              <button
                                type="button"
                                onClick={() => void handleOpenResult(result.id)}
                                className="rounded p-1 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
                                aria-label={t("LeftSideMenu.OpenResult")}
                                data-testid={`analysis-result-open-button-${result.id}`}
                              >
                                <ExternalLink className="h-4 w-4" />
                              </button>
                              {supportsOutput && (
                                <button
                                  type="button"
                                  onClick={() =>
                                    void handleOutputResult(
                                      result.id,
                                      result.resultType as OutputSupportedType,
                                      `${result.tableName} / ${result.name}`,
                                    )
                                  }
                                  className="rounded p-1 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
                                  aria-label={t("LeftSideMenu.OutputResult")}
                                  data-testid={`analysis-result-output-${result.id}`}
                                >
                                  <FileDown className="h-4 w-4" />
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() =>
                                  void handleDeleteResult(
                                    result.id,
                                    result.name,
                                  )
                                }
                                className="rounded p-1 text-white/60 transition-colors hover:bg-white/10 hover:text-red-300"
                                aria-label={t("LeftSideMenu.DeleteResult")}
                                data-testid={`analysis-result-delete-${result.id}`}
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              ))}
          </div>
        )}
      </div>

      {outputTarget?.type === "regression" && (
        <OutputResultDialog
          open={outputTarget !== null}
          onOpenChange={(open) => !open && setOutputTarget(null)}
          resultKind="regression"
          result={outputTarget.regressionResult}
        />
      )}

      {outputTarget?.type === "descriptive_statistics" && (
        <OutputResultDialog
          open={outputTarget !== null}
          onOpenChange={(open) => !open && setOutputTarget(null)}
          resultKind="descriptive_statistics"
          resultId={outputTarget.id}
          title={outputTarget.title}
        />
      )}

      {outputTarget?.type === "confidence_interval" && (
        <OutputResultDialog
          open={outputTarget !== null}
          onOpenChange={(open) => !open && setOutputTarget(null)}
          resultKind="confidence_interval"
          resultId={outputTarget.id}
          title={outputTarget.title}
        />
      )}
    </aside>
  );
};
