import { ConfidenceIntervalForm } from "@/components/organisms/Form/ConfidenceIntervalForm";
import { ConfidenceIntervalResult } from "@/components/organisms/Result/ConfidenceIntervalResult";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/organisms/Tab/BaseTab";
import { PageLayout } from "@/components/templates/PageLayout";
import { cn } from "@/lib/utils/helpers";
import { useConfidenceIntervalResultsStore } from "@/stores/confidenceIntervalResults";
import { useCurrentPageStore } from "@/stores/currentView";
import { X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type ConfidenceIntervalViewProps = {
  className?: string;
};

export const ConfidenceIntervalView = ({
  className,
}: ConfidenceIntervalViewProps) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<string>("analysis-settings");
  const results = useConfidenceIntervalResultsStore((s) => s.results);
  const removeResult = useConfidenceIntervalResultsStore((s) => s.removeResult);
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const handleAnalysisComplete = (resultIndex: number) => {
    setActiveTab(`result-${resultIndex}`);
  };

  const handleCloseResult = (id: string, index: number) => {
    removeResult(id);
    if (activeTab === `result-${index}`) {
      setActiveTab("analysis-settings");
    }
  };

  return (
    <PageLayout>
      <Tabs
        className={cn("flex min-h-0 w-full flex-1 flex-col", className)}
        value={activeTab}
        onValueChange={setActiveTab}
      >
        <TabsList>
          {/* 設定タブ */}
          <TabsTrigger value="analysis-settings">
            {t("ConfidenceIntervalView.FormTab")}
          </TabsTrigger>

          {/* 結果タブ */}
          {results.map((result, index) => (
            <TabsTrigger
              key={`result-${result.resultId}`}
              value={`result-${index}`}
            >
              <span>
                {t("ConfidenceIntervalView.ResultLabel", { number: index + 1 })}
              </span>
              <span
                role="button"
                tabIndex={0}
                aria-label={t("ConfidenceIntervalView.CloseResult")}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloseResult(result.resultId, index);
                }}
                onKeyDown={(e) => {
                  if (e.key !== "Enter" && e.key !== " ") return;
                  e.preventDefault();
                  e.stopPropagation();
                  handleCloseResult(result.resultId, index);
                }}
                className="ml-1.5 rounded p-0.5 opacity-60 hover:bg-white/20 hover:opacity-100 transition-opacity"
              >
                <X size={11} aria-hidden="true" />
              </span>
            </TabsTrigger>
          ))}
        </TabsList>

        {/* 設定タブコンテンツ */}
        <TabsContent
          value="analysis-settings"
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="flex min-h-0 flex-1 flex-col pt-4">
            <ConfidenceIntervalForm
              onCancel={handleCancel}
              onAnalysisComplete={handleAnalysisComplete}
            />
          </div>
        </TabsContent>

        {/* 結果タブコンテンツ */}
        {results.map((result, index) => (
          <TabsContent
            key={`result-${result.resultId}`}
            value={`result-${index}`}
            className="flex min-h-0 flex-1 flex-col"
          >
            <div className="app-scrollbar mx-auto w-full max-w-4xl overflow-y-auto pt-4">
              <ConfidenceIntervalResult result={result} />
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </PageLayout>
  );
};
