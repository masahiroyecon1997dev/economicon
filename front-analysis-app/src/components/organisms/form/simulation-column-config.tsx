import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { DistributionType, SimulationColumnSetting } from '../../../types/commonTypes';
import { InputText } from '../../atoms/Input/input-text';
import { Select } from '../../atoms/Input/Select';
import { SelectOption } from '../../atoms/Input/select-option';
import { FormField } from '../../molecules/Form/form-field';


type SimulationColumnConfigProps = {
  column: SimulationColumnSetting;
  index: number;
  distributionOptions: Array<{ value: DistributionType; label: string; params: string[] }>;
  onUpdate: (id: string, updates: Partial<SimulationColumnSetting>) => void;
  onDataTypeChange: (id: string, dataType: 'distribution' | 'fixed') => void;
  onDistributionTypeChange: (id: string, distributionType: DistributionType) => void;
  onDistributionParamChange: (id: string, param: string, value: number) => void;
  onRemove: (id: string) => void;
  canRemove: boolean;
  error: { columnName: string | undefined; distributionParams: Record<string, string | undefined> | undefined; fixedValue: string | undefined };
};

export const SimulationColumnConfig = ({
  column,
  index,
  distributionOptions,
  onUpdate,
  onDataTypeChange,
  onDistributionTypeChange,
  onDistributionParamChange,
  onRemove,
  canRemove,
  error,
}: SimulationColumnConfigProps) => {
  const { t } = useTranslation();
  const distOption = column.distributionType ? distributionOptions.find(d => d.value === column.distributionType) : null;

  const getParamLabel = (param: string): string => {
    const paramLabels: Record<string, string> = {
      'low': t('Common.MinValue'),
      'high': t('Common.MaxValue'),
      'mean': t('Common.Mean'),
      'deviation': t('Common.StandardDeviation'),
      'rate': t('Common.Rate'),
      'shape': t('Common.Shape'),
      'scale': t('Common.Scale'),
      'alpha': t('Common.Alpha'),
      'beta': t('Common.Beta'),
      'logMean': t('Common.LogMean'),
      'logSD': t('Common.LogStandardDeviation'),
      'trials': t('Common.NumberOfTrials'),
      'probability': t('Common.Probability'),
      'populationSize': t('Common.PopulationSize'),
      'numberOfSuccesses': t('Common.NumberOfSuccesses'),
      'sampleSize': t('Common.SampleSize')
    };
    return paramLabels[param] || param;
  };

  return (
    <div className="border border-border-color dark:border-gray-700 rounded-lg p-4 bg-secondary-main dark:bg-gray-900/30 overflow-y-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <div className="md:col-span-2 flex justify-between items-center">
          <p className="font-bold text-main dark:text-white">列 {index + 1}</p>
          <button
            onClick={() => onRemove(column.id)}
            className="text-gray-400 hover:text-red-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            disabled={!canRemove}
          >
            <X size={20} />
          </button>
        </div>

        <FormField label={t('CreateSimulationDataTableView.ColumnName')} htmlFor={`column-name-${column.id}`}>
          <InputText
            id={`column-name-${column.id}`}
            value={column.columnName}
            change={(e) => onUpdate(column.id, { columnName: e.target.value })}
            placeholder={t('CreateSimulationDataTableView.InputColumnName')}
            error={error.columnName}
          />
        </FormField>

        <FormField label={t('CreateSimulationDataTableView.DataType')} htmlFor={`data-type-${column.id}`}>
          <Select
            id={`data-type-${column.id}`}
            value={column.dataType}
            onChange={(e) => onDataTypeChange(column.id, e.target.value as 'distribution' | 'fixed')}
          >
            <SelectOption value="fixed">{t('Common.Constant')}</SelectOption>
            <SelectOption value="distribution">{t('Common.Distribution')}</SelectOption>
          </Select>
        </FormField>

        {column.dataType === 'distribution' && (
          <>
            <div className="md:col-span-2">
              <FormField label={t('CreateSimulationDataTableView.DistributionType')} htmlFor={`distribution-type-${column.id}`}>
                <Select
                  id={`distribution-type-${column.id}`}
                  value={column.distributionType || ''}
                  onChange={(e) => onDistributionTypeChange(column.id, e.target.value as DistributionType)}
                >
                  {distributionOptions.map(option => (
                    <SelectOption key={option.value} value={option.value}>
                      {t(option.label)}
                    </SelectOption>
                  ))}
                </Select>
              </FormField>
            </div>

            {distOption && (
              <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                {distOption.params.map(param => (
                  <FormField
                    key={param}
                    label={getParamLabel(param)}
                    htmlFor={`param-${param}-${column.id}`}
                  >
                    <InputText
                      id={`param-${param}-${column.id}`}
                      type="number"
                      step="0.01"
                      value={column.distributionParams?.[param]?.toString() || ''}
                      change={(e) => onDistributionParamChange(column.id, param, parseFloat(e.target.value))}
                      placeholder={`${getParamLabel(param)}${t('CreateSimulationDataTableView.InputDistributionParameters')}`}
                      error={error.distributionParams ? error.distributionParams[param] : undefined}
                    />
                  </FormField>
                ))}
              </div>
            )}
          </>
        )}

        {column.dataType === 'fixed' && (
          <div className="md:col-span-2 pt-2">
            <FormField label={t('CreateSimulationDataTableView.FixedValue')} htmlFor={`fixed-value-${column.id}`}>
              <InputText
                id={`fixed-value-${column.id}`}
                value={column.fixedValue?.toString() || ''}
                change={(e) => onUpdate(column.id, { fixedValue: e.target.value })}
                placeholder={t('CreateSimulationDataTableView.InputFixedValue')}
                error={error.fixedValue}
              />
            </FormField>
          </div>
        )}
      </div>
    </div>
  );
};
