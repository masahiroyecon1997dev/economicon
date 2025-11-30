import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DISTRIBUTION_OPTIONS } from "../../../common/constant";
import { createSimulationDataTable } from "../../../function/restApis";
import { validateColumnName, validateDistributionParam, validateNumRows, validateTableName } from "../../../function/validationFunctions";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useErrorDialogStore } from "../../../stores/useErrorDialogStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import type { DistributionType, SimulationColumnSetting } from "../../../types/commonTypes";
import { CancelButton } from "../../atoms/Button/CancelButton";
import { SubmitButton } from "../../atoms/Button/SubmitButton";
import { InputText } from "../../atoms/Input/InputText";
import { FormField } from "../../molecules/Form/FormField";
import { SimulationColumnConfig } from "../Form/SimulationColumnConfig";

export const CreateSimulationDataTableView = () => {
  const { t } = useTranslation();
  const { setCurrentView } = useCurrentViewStore();
  const { showErrorDialog } = useErrorDialogStore();
  const { setLoading, clearLoading } = useLoadingStore();
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
    let newValidateError = {
      tableName: validateTableName(tableName),
      numRows: validateNumRows(numRows),
    };
    setErrorMessage(newValidateError);
    let newColumns = structuredClone(columns);
    let columnErrorsExist = false;
    newColumns.map(col => {
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
      await showErrorDialog(t('Error.Error'), t('CreateSimulationDataTableView.FixValidationErrors'));
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
            case 'normal':
              distributionParams['loc'] = col.distributionParams?.mean;
              distributionParams['scale'] = col.distributionParams?.deviation;
              break;
            case 'exponential':
            case 'lognormal':
            case 'poisson':
            case 'binomial':
            case 'hypergeometric':
            case 'negativeBinomial':
              break;
            default:
          }
          return {
            columnName: col.columnName.trim(),
            dataType: col.dataType,
            distributionType: col.distributionType,
            distributionParams: col.distributionParams,
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
        setCurrentView('dataPreview');
      } else {
        await showErrorDialog('エラー', response.message || 'テーブルの作成に失敗しました。');
      }
    } catch (error) {
      console.error('Table creation error:', error);
      await showErrorDialog('エラー', 'テーブルの作成中にエラーが発生しました。');
    } finally {
      clearLoading();
    }
  };

  const handleCancel = () => {
    setCurrentView('selectFile');
  };
  return (
    <div className="mx-auto max-w-6xl overflow-y-auto max-h-full">
      <div className="flex flex-wrap justify-between gap-3 items-center mb-2">
        <h1 className="text-main dark:text-white text-4xl font-black leading-tight tracking-[-0.033em]">{t("CreateSimulationDataTableView.CreateNewDataTable")}</h1>
      </div>
      <p className="text-gray-600 dark:text-gray-400 text-base font-normal leading-normal mb-8">
        {t("CreateSimulationDataTableView.DefineYourTableNameAndRows")}
      </p>
      <div className="space-y-8">
        <div className="bg-white dark:bg-gray-800/50 p-6 rounded-lg border border-border-color dark:border-gray-700">
          <h2 className="text-main dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em] mb-6">{t("CreateSimulationDataTableView.TableSettings")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
        <div className="bg-white dark:bg-gray-800/50 p-6 rounded-lg border border-border-color dark:border-gray-700">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-main dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">列の設定</h2>
            <button
              onClick={addColumn}
              className="flex items-center gap-2 rounded-md bg-brand-primary text-white px-4 py-2 text-sm font-medium hover:bg-brand-primary-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary cursor-pointer"
            >
              <span className="material-symbols-outlined text-base"><FontAwesomeIcon icon={faPlus} /></span>
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
        <div className="flex justify-end items-center gap-4 pt-4">
          <CancelButton
            cancel={handleCancel}
          >
            {t("Common.Cancel")}
          </CancelButton>
          <SubmitButton
            submit={handleSubmit}
          >
            {t("CreateSimulationDataTableView.Submit")}
          </SubmitButton>
        </div>
      </div>
    </div>
  );
}
