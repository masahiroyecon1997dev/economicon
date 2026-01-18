import { Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DISTRIBUTION_OPTIONS } from "../../../constants/constant";
import { getTableInfo } from "../../../functions/internalFunctions";
import { createSimulationDataTable } from "../../../functions/restApis";
import { validateColumnName, validateDistributionParam, validateNumRows, validateTableName } from "../../../functions/validations";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { useMessageDialogStore } from "../../../stores/useMessageDialogStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { DistributionType, SimulationColumnSetting } from "../../../types/commonTypes";
import { InputText } from "../../atoms/Input/InputText";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../../molecules/Form/FormField";
import { SimulationColumnConfig } from "../../organisms/Form/SimulationColumnConfig";
import { MainViewLayout } from "../Layouts/MainViewLayout";

export const CreateSimulationDataTableView = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentViewStore(state => state.setCurrentView);
  const showMessageDialog = useMessageDialogStore(state => state.showMessageDialog);
  const setLoading = useLoadingStore(state => state.setLoading);
  const clearLoading = useLoadingStore(state => state.clearLoading);
  const addTableName = useTableListStore(state => state.addTableName);
  const addTableInfo = useTableInfosStore(state => state.addTableInfo);
  const COLUMN_SETTINGS_DEFAULT: SimulationColumnSetting = {
    id: '1',
    columnName: '',
    dataType: 'distribution',
    distributionType: 'uniform',
    distributionParams: { low: 0, high: 10 },
    fixedValue: '',
    errorMessage: { columnName: undefined, distributionParams: undefined, fixedValue: undefined },
  };
  const errorMessageInitial = {
    tableName: undefined,
    numRows: undefined,
  }
  const [tableName, setTableName] = useState('');
  const [numRows, setNumRows] = useState<number>(1000);
  const [columns, setColumns] = useState<SimulationColumnSetting[]>([
    COLUMN_SETTINGS_DEFAULT
  ]);
  const [errorMessage, setErrorMessage] = useState<
    {
      tableName: string | undefined,
      numRows: string | undefined,
    }>(errorMessageInitial);

  const addColumn = () => {
    const newColumn: SimulationColumnSetting = {
      ...COLUMN_SETTINGS_DEFAULT,
      id: Date.now().toString(),
    };
    setColumns([...columns, newColumn]);
  };

  const removeColumn = (id: string) => {
    setColumns(columns.filter(col => col.id !== id));
  };

  const updateColumn = (id: string, updates: Partial<SimulationColumnSetting>) => {
    setColumns(columns.map(col =>
      col.id === id ? { ...col, ...updates } : col
    ));
  };

  const handleDataTypeChange = (id: string, dataType: 'distribution' | 'fixed') => {
    const updates: Partial<SimulationColumnSetting> = {
      dataType: dataType,
    };

    if (dataType === 'distribution') {
      updates.distributionType = 'uniform';
      updates.distributionParams = { low: 0, high: 10 };
      delete updates.fixedValue;
    } else {
      updates.fixedValue = '';
      delete updates.distributionType;
      delete updates.distributionParams;
    }

    updateColumn(id, updates);
  };

  const handleDistributionTypeChange = (id: string, distributionType: DistributionType) => {
    const distOption = DISTRIBUTION_OPTIONS.find(d => d.value === distributionType);
    if (!distOption) return;

    const defaultParams: Record<string, number> = {};
    distOption.params.forEach(param => {
      switch (param) {
        case 'low': defaultParams[param] = 0; break;
        case 'high': defaultParams[param] = 10; break;
        case 'mean': defaultParams[param] = 0; break;
        case 'deviation': defaultParams[param] = 1; break;
        case 'rate': defaultParams[param] = 1; break;
        case 'scale': defaultParams[param] = 1; break;
        case 'alpha': defaultParams[param] = 2; break;
        case 'beta': defaultParams[param] = 2; break;
        case 'logMean': defaultParams[param] = 0; break;
        case 'logSD': defaultParams[param] = 1; break;
        case 'trials': defaultParams[param] = 10; break;
        case 'probability': defaultParams[param] = 0.5; break;
        case 'populationSize': defaultParams[param] = 20; break;
        case 'numberOfSuccesses': defaultParams[param] = 5; break;
        case 'sampleSize': defaultParams[param] = 10; break;
        default: defaultParams[param] = 1;
      }
    });

    updateColumn(id, {
      distributionType: distributionType,
      distributionParams: defaultParams
    });
  };

  const handleDistributionParamChange = (id: string, param: string, value: number) => {
    const column = columns.find(col => col.id === id);
    if (!column?.distributionParams) return;

    updateColumn(id, {
      distributionParams: {
        ...column.distributionParams,
        [param]: value
      }
    });
  };

  const validateInput = (): boolean => {
    const newValidateError = {
      tableName: validateTableName(tableName),
      numRows: validateNumRows(numRows),
    };
    setErrorMessage(newValidateError);
    let columnErrorsExist = false;
    const newColumns = columns.map(col => {
      const columnError = validateColumnName(col.columnName);
      const paramsError = validateDistributionParam(col.distributionType, col.distributionParams);
      if (columnError !== undefined || paramsError !== undefined) {
        columnErrorsExist = true;
      }
      return {
        ...col,
        errorMessage: {
          columnName: columnError,
          distributionParams: paramsError,
          fixedValue: undefined,
        }
      };
    });
    setColumns(newColumns);
    const topLevelErrorExists = Object.values(newValidateError).some(error => error !== undefined);
    // 一つでもエラーがあれば false を返す
    if (topLevelErrorExists || columnErrorsExist) {
      return false;
    }
    // エラーが一つもなければ true を返す
    return true;
  };

  const handleSubmit = async () => {
    if (!validateInput()) {
      await showMessageDialog(t('Error.Error'), t('ValidationMessages.FixValidationErrors'));
      return;
    }
    setLoading(true, t('CreateSimulationDataTableView.CreatingTable'));

    try {
      const columnSettings = columns.map(col => {
        if (col.dataType === 'distribution') {
          const distributionParams: Record<string, number> = {};
          switch (col.distributionType) {
            case 'uniform':
              distributionParams['low'] = col.distributionParams?.low;
              distributionParams['high'] = col.distributionParams?.high;
              break;
            case 'exponential':
              distributionParams['scale'] = col.distributionParams?.rate;
              break;
            case 'normal':
              distributionParams['loc'] = col.distributionParams?.mean;
              distributionParams['scale'] = col.distributionParams?.deviation;
              break;
            case 'gamma':
              distributionParams['shape'] = col.distributionParams?.shape;
              distributionParams['scale'] = col.distributionParams?.scale;
              break;
            case 'beta':
              distributionParams['a'] = col.distributionParams?.alpha;
              distributionParams['b'] = col.distributionParams?.beta;
              break;
            case 'weibull':
              distributionParams['a'] = col.distributionParams?.shape;
              distributionParams['scale'] = col.distributionParams?.scale;
              break;
            case 'lognormal':
              distributionParams['mean'] = col.distributionParams?.logMean;
              distributionParams['sigma'] = col.distributionParams?.logSD;
              break;
            case 'binomial':
              distributionParams['n'] = col.distributionParams?.trials;
              distributionParams['p'] = col.distributionParams?.probability;
              break;
            case 'bernoulli':
              distributionParams['p'] = col.distributionParams?.probability;
              break;
            case 'poisson':
              distributionParams['lam'] = col.distributionParams?.lambda;
              break;
            case 'geometric':
              distributionParams['p'] = col.distributionParams?.probability;
              break;
            case 'hypergeometric':
              distributionParams['N'] = col.distributionParams?.populationSize;
              distributionParams['K'] = col.distributionParams?.numberOfSuccesses;
              distributionParams['n'] = col.distributionParams?.sampleSize;
              break;
            default:
              break;
          }
          return {
            columnName: col.columnName.trim(),
            dataType: col.dataType,
            distributionType: col.distributionType,
            distributionParams: distributionParams,
          }
        } else {
          return {
            columnName: col.columnName.trim(),
            dataType: col.dataType,
            fixedValue: col.fixedValue,
          }
        }
      });

      const requestBody = {
        tableName: tableName.trim(),
        tableNumberOfRows: numRows,
        columnSettings: columnSettings
      };

      const response = await createSimulationDataTable(requestBody);

      if (response.code === 'OK') {
        const resTableInfo = await getTableInfo(response.result.tableName);
        setCurrentView('DataPreview');
        addTableName(response.result.tableName);
        addTableInfo(resTableInfo);
      } else {
        await showMessageDialog(t('Error.Error'), response.message || t('CreateSimulationDataTableView.TableCreationFailed'));
      }
    } catch {
      await showMessageDialog(t('Error.Error'), t('CreateSimulationDataTableView.TableCreationError'));
    } finally {
      clearLoading();
    }
  };

  const handleCancel = () => {
    setCurrentView('SelectFile');
  };
  return (
    <MainViewLayout
      title={t("CreateSimulationDataTableView.CreateNewDataTable")}
      description={t("CreateSimulationDataTableView.DefineYourTableNameAndRows")}
    >
      <div className="space-y-6">
        <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700">
          <h2 className="text-main dark:text-white text-base font-bold leading-tight mb-4">{t("CreateSimulationDataTableView.TableSettings")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              label={t("CreateSimulationDataTableView.TableName")}
              htmlFor="table-name"
            >
              <InputText
                id="table-name"
                value={tableName}
                change={(e) => setTableName(e.target.value)}
                placeholder={t("CreateSimulationDataTableView.TableNamePlaceholder")}
                error={errorMessage.tableName}
              />
            </FormField>

            <FormField
              label={t("CreateSimulationDataTableView.NumberOfRows")}
              htmlFor="row-count"
            >
              <InputText
                id="row-count"
                type="number"
                value={numRows.toString()}
                change={(e) => setNumRows(parseInt(e.target.value) || 0)}
                placeholder="1000"
                error={errorMessage.numRows}
              />
            </FormField>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-main dark:text-white text-base font-bold leading-tight">列の設定</h2>
            <button
              onClick={addColumn}
              className="flex items-center gap-2 rounded-md bg-brand-primary text-white px-3 py-1.5 text-sm font-medium hover:bg-brand-primary-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary cursor-pointer"
            >
              <Plus size={16} />
              {t("CreateSimulationDataTableView.AddColumn")}
            </button>
          </div>
          <div className="space-y-4 overflow-y-auto max-h-64">
            {columns.map((column, index) => (
              <SimulationColumnConfig
                key={column.id}
                column={column}
                index={index}
                distributionOptions={DISTRIBUTION_OPTIONS}
                onUpdate={updateColumn}
                onDataTypeChange={handleDataTypeChange}
                onDistributionTypeChange={handleDistributionTypeChange}
                onDistributionParamChange={handleDistributionParamChange}
                onRemove={removeColumn}
                canRemove={columns.length > 1}
                error={column.errorMessage}
              />
            ))}
          </div>
        </div>
        <ActionButtonBar
          cancelText={t('Common.Cancel')}
          selectText={t('CreateSimulationDataTableView.Submit')}
          onCancel={handleCancel}
          onSelect={handleSubmit}
        />
      </div>
    </MainViewLayout>
  );
}
