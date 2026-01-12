import { useActionState, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../../functions/messageDialog";
import { linearRegression } from "../../../functions/restApis";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { LinearRegressionResultType } from "../../../types/commonTypes";
import { Select, SelectItem } from "../../atoms/Input/Select";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../../molecules/Form/FormField";
import { MainViewLayout } from "../Layouts/MainViewLayout";

type FormState = {
  errors?: {
    tableName?: string;
    dependentVariable?: string;
    explanatoryVariables?: string;
  };
  success?: boolean;
  result?: LinearRegressionResultType;
};

export const LinearRegressionFormView2 = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const { selectedTableName, setSelectedTableName, columnList, setColumnList } = useTableColumnLoader({
    numericOnly: false,
    autoLoadOnMount: true,
  });

  const [dependentVariable, setDependentVariable] = useState<string>("");
  const [explanatoryVariables, setExplanatoryVariables] = useState<string[]>([]);

  // アクション関数: フォーム送信時の処理
  async function submitLinearRegressionAction(
    _prevState: FormState,
    formData: FormData
  ): Promise<FormState> {
    const tableName = formData.get("tableName") as string;
    const dependentVariable = formData.get("dependentVariable") as string;
    const explanatoryVariablesData = formData.getAll("explanatoryVariables") as string[];

    // バリデーション
    const errors: {
      tableName?: string;
      dependentVariable?: string;
      explanatoryVariables?: string;
    } = {};

    if (!tableName || tableName.trim() === "") {
      errors.tableName = t("LinearRegressionFormView.Validation.TableNameRequired");
    }

    if (!dependentVariable || dependentVariable.trim() === "") {
      errors.dependentVariable = t("LinearRegressionFormView.Validation.DependentVariableRequired");
    }

    if (explanatoryVariablesData.length === 0) {
      errors.explanatoryVariables = t("LinearRegressionFormView.Validation.ExplanatoryVariablesRequired");
    }

    if (Object.keys(errors).length > 0) {
      return { errors };
    }

    // API呼び出し
    try {
      const response = await linearRegression({
        tableName,
        dependentVariable,
        explanatoryVariables: explanatoryVariablesData,
      });

      if (response.code === "OK") {

      } else {
        await showMessageDialog(t("Error.Error"), response.message || t("Error.UnexpectedError"));
        return { errors: { tableName: response.message || t("Error.UnexpectedError") } };
      }
    } catch {
      await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
      return { errors: { tableName: t("Error.UnexpectedError") } };
    }
  }

  const [state, formAction, isPending] = useActionState<FormState, FormData>(
    submitLinearRegressionAction,
    { errors: undefined, success: false }
  );

  // 成功時の処理: 結果モーダルを表示してからビュー遷移
  useEffect(() => {
    if (state.success && state.result) {
      const displayResult = async () => {
        const resultMessage = formatResultMessage(state.result);
        await showMessageDialog(t("Common.OK"), resultMessage);
        setCurrentView("DataPreview");
      };
      displayResult();
    }
  }, [state.success, state.result, setCurrentView, t]);

  // 結果を整形して表示用メッセージを作成
  const formatResultMessage = (result: LinearRegressionResult): string => {
    const stats = result.modelStatistics;
    let message = `${t("LinearRegressionFormView.AnalysisSuccess")}\n\n`;
    message += `${t("LinearRegressionFormView.TableName")}: ${result.tableName}\n`;
    message += `${t("LinearRegressionFormView.DependentVariable")}: ${result.dependentVariable}\n`;
    message += `${t("LinearRegressionFormView.ExplanatoryVariables")}: ${result.explanatoryVariables.join(", ")}\n\n`;
    message += `=== ${t("LinearRegressionFormView.ModelStatistics")} ===\n`;
    message += `R²: ${stats.R2.toFixed(4)}\n`;
    message += `Adjusted R²: ${stats.adjustedR2.toFixed(4)}\n`;
    message += `AIC: ${stats.AIC.toFixed(4)}\n`;
    message += `BIC: ${stats.BIC.toFixed(4)}\n`;
    message += `F-statistic: ${stats.fValue.toFixed(4)}\n`;
    message += `F-probability: ${stats.fProbability.toFixed(4)}\n`;
    message += `Log-Likelihood: ${stats.logLikelihood.toFixed(4)}\n`;
    message += `Observations: ${stats.nObservations}\n\n`;
    message += `=== ${t("LinearRegressionFormView.Parameters")} ===\n`;
    result.parameters.forEach((param) => {
      message += `\n${param.variable}:\n`;
      message += `  Coefficient: ${param.coefficient.toFixed(4)}\n`;
      message += `  Std Error: ${param.standardError.toFixed(4)}\n`;
      message += `  t-value: ${param.tValue.toFixed(4)}\n`;
      message += `  P-value: ${param.pValue.toFixed(4)}\n`;
    });
    return message;
  };

  const handleTableChange = async (value: string) => {
    setSelectedTableName(value);
    setDependentVariable("");
    setExplanatoryVariables([]);

    if (!value) {
      setColumnList([]);
    }
  };

  const handleDependentVariableChange = (columnName: string) => {
    setDependentVariable(columnName);
  };

  const handleExplanatoryVariableToggle = (columnName: string) => {
    setExplanatoryVariables((prev) => {
      if (prev.includes(columnName)) {
        return prev.filter((v) => v !== columnName);
      } else {
        return [...prev, columnName];
      }
    });
  };

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  const handleFormSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    formAction(formData);
  };

  return (
    <MainViewLayout
      maxWidth="4xl"
      title={t("LinearRegressionFormView.Title")}
      description={t("LinearRegressionFormView.Description")}
    >
      <form onSubmit={handleFormSubmit}>
        {/* Hidden inputs for form data */}
        <input type="hidden" name="tableName" value={selectedTableName} />
        <input type="hidden" name="dependentVariable" value={dependentVariable} />
        {explanatoryVariables.map((variable, index) => (
          <input key={index} type="hidden" name="explanatoryVariables" value={variable} />
        ))}

        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
            <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
              {t("LinearRegressionFormView.SelectDataTable")}
            </h2>
            <div>
              <FormField label={t("LinearRegressionFormView.DataTable")} htmlFor="data-table">
                <Select id="data-table"
                  name="tableName"
                  value={selectedTableName}
                  onValueChange={handleTableChange}
                  disabled={isPending}
                >
                  <SelectItem value="" disabled>
                    {t("LinearRegressionFormView.SelectATable")}
                  </SelectItem>
                  {tableList.map((table, index) => (
                    <SelectItem key={index} value={table}>
                      {table}
                    </SelectItem>
                  ))}
                </Select>
              </FormField>
              {/* <label className="mb-2 block text-sm font-medium text-text-main" htmlFor="data-table">
                {t("LinearRegressionFormView.DataTable")}
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 py-1.5 px-2.5 text-sm text-text-main shadow-sm focus:border-accent focus:ring-accent"
                id="data-table"
                name="tableName"
                value={selectedTableName}
                onChange={handleTableChange}
                disabled={isPending}
              >
                <option value="" disabled>
                  {t("LinearRegressionFormView.SelectATable")}
                </option>
                {tableList.map((table, index) => (
                  <option key={index} value={table}>
                    {table}
                  </option>
                ))}
              </select>
              {state.errors?.tableName && (
                <p className="mt-1 text-xs text-red-600">{state.errors.tableName}</p>
              )} */}
            </div>
          </div>
          <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
            <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">
              {t("LinearRegressionFormView.SelectVariables")}
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-main">
                  {t("LinearRegressionFormView.DependentVariable")}
                </label>
                <p className="mb-2 text-xs text-text-main/60">
                  {t("LinearRegressionFormView.DependentVariableDescription")}
                </p>
                <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                  <ul className="flex flex-col gap-1">
                    {columnList.map((column, index) => (
                      <li key={index}>
                        <label className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                          <input
                            className="h-4 w-4 border-gray-300 text-accent focus:ring-accent"
                            name="dependent-variable"
                            type="radio"
                            value={column.name}
                            checked={dependentVariable === column.name}
                            onChange={(e) => handleDependentVariableChange(e.target.value)}
                            disabled={isPending}
                          />
                          <span>{column.name}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
                {state.errors?.dependentVariable && (
                  <p className="mt-1 text-xs text-red-600">{state.errors.dependentVariable}</p>
                )}
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-text-main">
                  {t("LinearRegressionFormView.ExplanatoryVariables")}
                </label>
                <p className="mb-2 text-xs text-text-main/60">
                  {t("LinearRegressionFormView.ExplanatoryVariablesDescription")}
                </p>
                <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                  <ul className="flex flex-col gap-1">
                    {columnList.map((column, index) => (
                      <li key={index}>
                        <label className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                          <input
                            className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
                            type="checkbox"
                            value={column.name}
                            checked={explanatoryVariables.includes(column.name)}
                            onChange={(e) => handleExplanatoryVariableToggle(e.target.value)}
                            disabled={isPending}
                          />
                          <span>{column.name}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                </div>
                {state.errors?.explanatoryVariables && (
                  <p className="mt-1 text-xs text-red-600">{state.errors.explanatoryVariables}</p>
                )}
              </div>
            </div>
            <div className="mt-4">
              <label className="mb-1.5 block text-xs font-medium text-text-main">
                {t("LinearRegressionFormView.SelectedExplanatoryVariables")}
              </label>
              <div className="flex flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-2 min-h-11">
                {explanatoryVariables.map((variable, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-md bg-accent text-white text-xs"
                  >
                    {variable}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <ActionButtonBar
            cancelText={t("Common.Cancel")}
            selectText={isPending ? t("LinearRegressionFormView.Processing") : t("LinearRegressionFormView.RunAnalysis")}
            onCancel={handleCancel}
            onSelect={() => { }}
          />
        </div>
      </form>
    </MainViewLayout>
  );
};
