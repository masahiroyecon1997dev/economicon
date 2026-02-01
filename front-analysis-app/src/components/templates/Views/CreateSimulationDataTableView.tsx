import { zodResolver } from "@hookform/resolvers/zod";
import { Edit2, Plus, Trash2 } from "lucide-react";
import { startTransition, useActionState, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { DISTRIBUTION_OPTIONS } from "../../../constants/constant";
import { getTableInfo } from "../../../functions/internalFunctions";
import { showMessageDialog } from "../../../functions/messageDialog";
import { createSimulationDataTable } from "../../../functions/restApis";
import { validateDistributionParam } from "../../../functions/validations";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { useTableListStore } from "../../../stores/useTableListStore";
import type { DistributionType, SimulationColumnSetting } from "../../../types/commonTypes";
import { InputText } from "../../atoms/Input/InputText";
import { ActionButtonBar } from "../../molecules/ActionBar/ActionButtonBar";
import { FormField } from "../../molecules/Form/FormField";
import { SimulationColumnEditDialog } from "../../organisms/Modal/SimulationColumnEditDialog";
import { MainViewLayout } from "../Layouts/MainViewLayout";

const createSimulationSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z.string().min(1, t("ValidationMessages.TableNameRequired")),
    numRows: z.number().min(1, t("ValidationMessages.NumRowsMoreThan0")),
  });

type SimulationFormData = z.infer<ReturnType<typeof createSimulationSchema>>;

export const CreateSimulationDataTableView = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentViewStore(state => state.setCurrentView);
  const addTableName = useTableListStore(state => state.addTableName);
  const addTableInfo = useTableInfosStore(state => state.addTableInfo);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SimulationFormData>({
    resolver: zodResolver(createSimulationSchema(t)),
    defaultValues: {
      tableName: "",
      numRows: 1000,
    },
  });

  const tableName = watch("tableName");
  const numRows = watch("numRows");

  const COLUMN_SETTINGS_DEFAULT: SimulationColumnSetting = {
    id: '1',
    columnName: '',
    dataType: 'distribution',
    distributionType: 'uniform',
    distributionParams: { low: 0, high: 10 },
    fixedValue: '',
    errorMessage: { columnName: undefined, distributionParams: undefined, fixedValue: undefined },
  };

  const [columns, setColumns] = useState<SimulationColumnSetting[]>([
    COLUMN_SETTINGS_DEFAULT
  ]);

  const [editingColumnId, setEditingColumnId] = useState<string | null>(null);

  type ActionState = {
    success: boolean;
  };

  const handleSimulationAction = async (
    _prevState: ActionState,
    formData: FormData
  ): Promise<ActionState> => {
    const tableName = formData.get("tableName") as string;
    const numRows = parseInt(formData.get("numRows") as string);
    const columnsJson = formData.get("columns") as string;
    const columns: SimulationColumnSetting[] = JSON.parse(columnsJson);

    // カラムのバリデーション
    let hasError = false;
    const validatedColumns = columns.map(col => {
      const errors: {
        columnName: string | undefined;
        distributionParams: Record<string, string | undefined> | undefined;
        fixedValue: string | undefined;
      } = {
        columnName: undefined,
        distributionParams: undefined,
        fixedValue: undefined,
      };

      if (!col.columnName || col.columnName.trim() === "") {
        errors.columnName = t("ValidationMessages.ColumnNameRequired");
        hasError = true;
      }

      if (col.dataType === "distribution") {
        const paramsError = validateDistributionParam(col.distributionType, col.distributionParams);
        if (paramsError !== undefined) {
          hasError = true;
        }
      }
      return { ...col, errorMessage: errors };
    });

    if (hasError) {
      setColumns(validatedColumns);
      await showMessageDialog(t("Error.Error"), t("ValidationMessages.FixValidationErrors"));
      return { success: false };
    }

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
        addTableName(response.result.tableName);
        addTableInfo(resTableInfo);
        setCurrentView('DataPreview');
        return { success: true };
      } else {
        await showMessageDialog(t('Error.Error'), response.message || t('CreateSimulationDataTableView.TableCreationFailed'));
        return { success: false };
      }
    } catch (error) {
      let errorMessage = t('CreateSimulationDataTableView.TableCreationError');
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      await showMessageDialog(t('Error.Error'), errorMessage);
      return { success: false };
    }
  };

  const [, submitAction, isPending] = useActionState(handleSimulationAction, {
    success: false,
  });

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

  const onSubmit = (data: SimulationFormData) => {
    const formData = new FormData();
    formData.append("tableName", data.tableName);
    formData.append("numRows", data.numRows.toString());
    formData.append("columns", JSON.stringify(columns));
    startTransition(() => {
      submitAction(formData);
    });
  };

  const handleCancel = () => {
    setCurrentView('ImportDataFile');
  };

  const getColumnSummary = (column: SimulationColumnSetting): string => {
    if (column.dataType === 'fixed') {
      return `${column.columnName || t('CreateSimulationDataTableView.NotSet')} - ${t('Common.Constant')}: ${column.fixedValue || t('CreateSimulationDataTableView.NotSet')}`;
    }

    const distOption = DISTRIBUTION_OPTIONS.find(d => d.value === column.distributionType);
    if (!distOption) {
      return `${column.columnName || t('CreateSimulationDataTableView.NotSet')} - ${t('Common.Distribution')}`;
    }

    const paramsStr = distOption.params
      .map(param => `${param}=${column.distributionParams?.[param] ?? '?'}`)
      .join(', ');

    return `${column.columnName || t('CreateSimulationDataTableView.NotSet')} - ${t(distOption.label)} (${paramsStr})`;
  };

  return (
    <MainViewLayout
      title={t("CreateSimulationDataTableView.CreateNewDataTable")}
      description={t("CreateSimulationDataTableView.DefineYourTableNameAndRows")}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                change={(e) => setValue("tableName", e.target.value, { shouldValidate: true })}
                placeholder={t("CreateSimulationDataTableView.TableNamePlaceholder")}
                error={errors.tableName?.message}
                disabled={isPending}
                {...register("tableName")}
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
                change={(e) => setValue("numRows", parseInt(e.target.value) || 0, { shouldValidate: true })}
                placeholder="1000"
                error={errors.numRows?.message}
                disabled={isPending}
                {...register("numRows")}
              />
            </FormField>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800/50 p-4 rounded-lg border border-border-color dark:border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-main dark:text-white text-base font-bold leading-tight">{t('CreateSimulationDataTableView.ColumnSettings')}</h2>
            <button
              type="button"
              onClick={addColumn}
              className="flex items-center gap-2 rounded-md bg-brand-primary text-white px-3 py-1.5 text-sm font-medium hover:bg-brand-primary-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-primary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isPending}
            >
              <Plus size={16} />
              {t("CreateSimulationDataTableView.AddColumn")}
            </button>
          </div>
          <div className="space-y-0 max-h-48 overflow-y-auto">
            {columns.map((column, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 px-3 border-t border-gray-300 dark:border-gray-600 first:border-t-0"
              >
                <span className="text-sm text-gray-700 dark:text-gray-300 flex-1 mr-4">
                  {getColumnSummary(column)}
                </span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingColumnId(column.id)}
                    className="flex items-center gap-1 text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    disabled={isPending}
                    aria-label={t('Common.Edit')}
                  >
                    <Edit2 size={16} />
                    {t('Common.Edit')}
                  </button>
                  {columns.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeColumn(column.id)}
                      className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                      disabled={isPending}
                      aria-label={t('Common.Delete')}
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        <ActionButtonBar
          cancelText={t('Common.Cancel')}
          selectText={
            isPending
              ? t('CreateSimulationDataTableView.CreatingTable')
              : t('CreateSimulationDataTableView.Submit')
          }
          onCancel={handleCancel}
          onSelect={() => { }}
          onSelectType="submit"
        />
      </form>

      {editingColumnId && (
        <SimulationColumnEditDialog
          isOpen={!!editingColumnId}
          column={columns.find(col => col.id === editingColumnId)!}
          index={columns.findIndex(col => col.id === editingColumnId)}
          distributionOptions={DISTRIBUTION_OPTIONS}
          onUpdate={updateColumn}
          onDataTypeChange={handleDataTypeChange}
          onDistributionTypeChange={handleDistributionTypeChange}
          onDistributionParamChange={handleDistributionParamChange}
          onRemove={(id) => {
            removeColumn(id);
            setEditingColumnId(null);
          }}
          onClose={() => setEditingColumnId(null)}
          canRemove={columns.length > 1}
          error={columns.find(col => col.id === editingColumnId)?.errorMessage || {
            columnName: undefined,
            distributionParams: undefined,
            fixedValue: undefined
          }}
          disabled={isPending}
        />
      )}
    </MainViewLayout>
  );
}
