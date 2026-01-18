import { useActionState, useState } from "react";
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

type ActionState = {
  results: LinearRegressionResultType[];
};

export const RegressionView = ({ className }: RegressionViewProps) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<string>("analysis-settings");
  const tableList = useTableListStore((state) => state.tableList);
  const { selectedTableName, setSelectedTableName, columnList, setColumnList } =
    useTableColumnLoader({
      numericOnly: false,
      autoLoadOnMount: true,
    });
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const handleTableChange = async (value: string) => {
    setSelectedTableName(value);
    if (!value) {
      setColumnList([]);
    }
  };

  const handleCancel = () => {
    setCurrentView("DataPreview"); // または適切なビューへ遷移
  };

  const handleRegressionAction = async (
    prevState: ActionState,
    formData: FormData
  ): Promise<ActionState> => {
    const tableName = formData.get("tableName") as string;
    const dependentVariable = formData.get("dependentVariable") as string;
    const explanatoryVariablesStr = formData.get("explanatoryVariables") as string;
    const explanatoryVariables = explanatoryVariablesStr
      ? explanatoryVariablesStr.split(",")
      : [];
    console.log(tableName, dependentVariable, explanatoryVariables);
    try {
      const response = await linearRegression({
        tableName,
        dependentVariable,
        explanatoryVariables,
      });

      if (response.code === "OK" && response.result) {
        // 新しい結果を配列の末尾に追加
        const newResults = [...prevState.results, response.result];
        // 最新の結果タブに切り替え
        setActiveTab(`result-${newResults.length - 1}`);
        return { results: newResults };
      } else {
        await showMessageDialog(
          t("Error.Error"),
          response.message || t("Error.UnexpectedError")
        );
        return prevState;
      }
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      return prevState;
    }
  };

  const [state, submitAction, isPending] = useActionState(handleRegressionAction, {
    results: [],
  });

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
          {state.results.map((_, index) => (
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
              action={submitAction}
              onCancel={handleCancel}
              isPending={isPending}
            />
          </div>
        </TabsContent>

        {/* 結果タブコンテンツ */}
        {state.results.map((result, index) => (
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
