import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils/helpers";
import { useCurrentPageStore } from "../../stores/currentView";
import { useRegressionResultsStore } from "../../stores/regressionResults";
import { LinearRegressionForm } from "../organisms/Form/LinearRegressionForm";
import { RegressionResult } from "../organisms/Result/RegressionResult";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../organisms/Tab/BaseTab";
import { PageLayout } from "../templates/PageLayout";

type RegressionProps = {
  className?: string;
};

export const Regression = ({ className }: RegressionProps) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<string>("analysis-settings");
  const results = useRegressionResultsStore((state) => state.results);
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const handleAnalysisComplete = (resultIndex: number) => {
    setActiveTab(`result-${resultIndex}`);
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
            {t("RegressionTab.FormTab")}
          </TabsTrigger>

          {/* 結果タブ */}
          {results.map((_, index) => (
            <TabsTrigger key={`result-${index}`} value={`result-${index}`}>
              {t("RegressionTab.ResultLabel", { number: index + 1 })}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* 設定タブコンテンツ */}
        <TabsContent
          value="analysis-settings"
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="flex min-h-0 flex-1 flex-col pt-4">
            <LinearRegressionForm
              onCancel={handleCancel}
              onAnalysisComplete={handleAnalysisComplete}
            />
          </div>
        </TabsContent>

        {/* 結果タブコンテンツ */}
        {results.map((result, index) => (
          <TabsContent
            key={`result-${index}`}
            value={`result-${index}`}
            className="flex min-h-0 flex-1 flex-col"
          >
            <div className="mx-auto w-full max-w-6xl overflow-y-auto pt-4">
              <RegressionResult result={result} />
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </PageLayout>
  );
};
