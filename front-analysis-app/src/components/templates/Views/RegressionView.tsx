import { useState } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../../functions/messageDialog";
import { linearRegression } from "../../../functions/restApis";
import { cn } from "../../../functions/utils";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { LinearRegressionResultType } from "../../../types/commonTypes";
import { LinearRegressionForm } from "../../organisms/Form/LinearRegressionForm";
import { RegressionResult } from "../../organisms/Result/RegressionResult";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../organisms/Tab/BaseTab";
import { MainViewLayout } from "../Layouts/MainViewLayout";

type RegressionViewProps = {
  className?: string;
};


export const RegressionView = ({ className }: RegressionViewProps) => {
  const { t } = useTranslation();
  const [results, setResults] = useState<LinearRegressionResultType[]>([]);
  const [activeTab, setActiveTab] = useState<string>("analysis-settings");
  const tableList = useTableListStore((state) => state.tableList);
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
    });
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const [isPending, setIsPending] = useState(false);

  const handleTableChange = async (value: string) => {
    setSelectedTableName(value);
    if (!value) {
      setColumnList([]);
    }
  };

  const handleCancel = () => {
    setCurrentView("DataPreview"); // または適切なビューへ遷移
  };

  const handleFormSubmit = async (data: {
    tableName: string;
    dependentVariable: string;
    explanatoryVariables: string[];
  }) => {
    setIsPending(true);

    try {
      const response = await linearRegression({
        tableName: data.tableName,
        dependentVariable: data.dependentVariable,
        explanatoryVariables: data.explanatoryVariables,
      });

      if (response.code === "OK" && response.result) {
        // 新しい結果を配列の末尾に追加
        setResults((prev) => [...prev, response.result]);
        // 最新の結果タブ（results初期長=0ならindex0 -> result-0）
        // 追加後の配列長-1 が新しいインデックス
        setActiveTab(`result-${results.length}`);
      } else {
        await showMessageDialog(
          t("Error.Error"),
          response.message || t("Error.UnexpectedError")
        );
      }
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
    } finally {
      setIsPending(false);
    }
  };

  return (
    <MainViewLayout>
      <Tabs
        className={cn("flex w-full flex-col", className)}
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
        <TabsContent value="analysis-settings">
          <div className="mx-auto max-w-4xl pt-6">
            <LinearRegressionForm
              tableList={tableList}
              selectedTableName={selectedTableName}
              columns={columnList}
              onTableChange={handleTableChange}
              onSubmit={handleFormSubmit}
              onCancel={handleCancel}
              isPending={isPending}
            />
          </div>
        </TabsContent>

        {/* 結果タブコンテンツ */}
        {results.map((result, index) => (
          <TabsContent key={`result-${index}`} value={`result-${index}`}>
            <div className="mx-auto max-w-6xl pt-6">
              <RegressionResult result={result} />
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </MainViewLayout>
  );
};
