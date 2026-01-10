import { useState } from "react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../../function/messageDialog";
import { linearRegression } from "../../../function/restApis";
import { useTableColumnLoader } from "../../../hooks/useTableColumnLoader";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import { ActionButtonBar } from "../../molecules/action-bar/action-button-bar";
import { MainViewLayout } from "../../templates/layouts/main-view-layout";

export const LinearRegressionFormView = () => {
  const { t } = useTranslation();
  const tableList = useTableListStore((state) => state.tableList);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
  const { setLoading, clearLoading } = useLoadingStore();

  const { selectedTableName, setSelectedTableName, columnList, setColumnList } = useTableColumnLoader({
    numericOnly: false,
    autoLoadOnMount: true,
  });

  const [dependentVariable, setDependentVariable] = useState<string>("");
  const [explanatoryVariables, setExplanatoryVariables] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<{
    tableName?: string;
    dependentVariable?: string;
    explanatoryVariables?: string;
  }>({});

  const handleTableChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedTable = event.target.value;
    setSelectedTableName(selectedTable);
    setDependentVariable("");
    setExplanatoryVariables([]);
    setErrorMessage({});

    if (!selectedTable) {
      setColumnList([]);
    }
  };

  const handleDependentVariableChange = (columnName: string) => {
    setDependentVariable(columnName);
    setErrorMessage(prev => ({ ...prev, dependentVariable: undefined }));
  };

  const handleExplanatoryVariableToggle = (columnName: string) => {
    setExplanatoryVariables(prev => {
      if (prev.includes(columnName)) {
        return prev.filter(v => v !== columnName);
      } else {
        return [...prev, columnName];
      }
    });
    setErrorMessage(prev => ({ ...prev, explanatoryVariables: undefined }));
  };

  const validateInput = (): boolean => {
    const errors: {
      tableName?: string;
      dependentVariable?: string;
      explanatoryVariables?: string;
    } = {};

    if (!selectedTableName || selectedTableName.trim() === '') {
      errors.tableName = t('LinearRegressionFormView.Validation.TableNameRequired');
    }

    if (!dependentVariable || dependentVariable.trim() === '') {
      errors.dependentVariable = t('LinearRegressionFormView.Validation.DependentVariableRequired');
    }

    if (explanatoryVariables.length === 0) {
      errors.explanatoryVariables = t('LinearRegressionFormView.Validation.ExplanatoryVariablesRequired');
    }

    setErrorMessage(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateInput()) {
      return;
    }

    setLoading(true, t('LinearRegressionFormView.RunningAnalysis'));

    try {
      const response = await linearRegression({
        tableName: selectedTableName,
        dependentVariable: dependentVariable,
        explanatoryVariables: explanatoryVariables,
      });

      if (response.code === 'OK') {
        await showMessageDialog(t('Common.OK'), t('LinearRegressionFormView.AnalysisSuccess'));
        setCurrentView('DataPreview');
      } else {
        await showMessageDialog(t('Error.Error'), response.message || t('Error.UnexpectedError'));
      }
    } catch {
      await showMessageDialog(t('Error.Error'), t('Error.UnexpectedError'));
    } finally {
      clearLoading();
    }
  };

  const handleCancel = () => {
    setCurrentView('DataPreview');
  };



  return (
    <MainViewLayout
      maxWidth="4xl"
      title={t('LinearRegressionFormView.Title')}
      description={t('LinearRegressionFormView.Description')}
    >
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
          <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">{t('LinearRegressionFormView.SelectDataTable')}</h2>
          <div>
            <label className="mb-2 block text-sm font-medium text-text-main" htmlFor="data-table">{t('LinearRegressionFormView.DataTable')}</label>
            <select
              className="w-full rounded-lg border border-gray-300 py-1.5 px-2.5 text-sm text-text-main shadow-sm focus:border-accent focus:ring-accent"
              id="data-table"
              value={selectedTableName}
              onChange={handleTableChange}
            >
              <option value="" disabled>{t('LinearRegressionFormView.SelectATable')}</option>
              {tableList.map((table, index) => (
                <option key={index} value={table}>{table}</option>
              ))}
            </select>
            {errorMessage.tableName && (
              <p className="mt-1 text-xs text-red-600">{errorMessage.tableName}</p>
            )}
          </div>
        </div>
        <div className="rounded-xl border border-border-color bg-white p-3 shadow-sm">
          <h2 className="mb-2 text-sm font-bold leading-tight text-text-heading">{t('LinearRegressionFormView.SelectVariables')}</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-main">{t('LinearRegressionFormView.DependentVariable')}</label>
              <p className="mb-2 text-xs text-text-main/60">{t('LinearRegressionFormView.DependentVariableDescription')}</p>
              <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                <ul className="flex flex-col gap-1">
                  {columnList.map((column, index) => (
                    <li key={index}>
                      <label
                        className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                        <input
                          className="h-4 w-4 border-gray-300 text-accent focus:ring-accent"
                          name="dependent-variable"
                          type="radio"
                          value={column.name}
                          checked={dependentVariable === column.name}
                          onChange={(e) => handleDependentVariableChange(e.target.value)}
                        />
                        <span>{column.name}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
              {errorMessage.dependentVariable && (
                <p className="mt-1 text-xs text-red-600">{errorMessage.dependentVariable}</p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-text-main">{t('LinearRegressionFormView.ExplanatoryVariables')}</label>
              <p className="mb-2 text-xs text-text-main/60">{t('LinearRegressionFormView.ExplanatoryVariablesDescription')}</p>
              <div className="h-64 overflow-y-auto rounded-lg border border-border-color bg-secondary p-2">
                <ul className="flex flex-col gap-1">
                  {columnList.map((column, index) => (
                    <li key={index}>
                      <label
                        className="flex w-full cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-white">
                        <input
                          className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
                          type="checkbox"
                          value={column.name}
                          checked={explanatoryVariables.includes(column.name)}
                          onChange={(e) => handleExplanatoryVariableToggle(e.target.value)}
                        />
                        <span>{column.name}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </div>
              {errorMessage.explanatoryVariables && (
                <p className="mt-1 text-xs text-red-600">{errorMessage.explanatoryVariables}</p>
              )}
            </div>
          </div>
          <div className="mt-4">
            <label className="mb-1.5 block text-xs font-medium text-text-main">{t('LinearRegressionFormView.SelectedExplanatoryVariables')}</label>
            <div className="flex flex-wrap gap-2 rounded-lg border border-border-color bg-secondary p-2 min-h-11">
              {explanatoryVariables.map((variable, index) => (
                <span key={index} className="inline-flex items-center px-2 py-1 rounded-md bg-accent text-white text-xs">
                  {variable}
                </span>
              ))}
            </div>
          </div>
        </div>
        <ActionButtonBar
          cancelText={t('Common.Cancel')}
          selectText={t('LinearRegressionFormView.RunAnalysis')}
          onCancel={handleCancel}
          onSelect={handleSubmit}
        />
      </div>
    </MainViewLayout>
  );
}
