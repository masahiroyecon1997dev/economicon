import { useTranslation } from 'react-i18next';
import { InputText } from '../../atoms/Input/InputText';
import { Select } from '../../atoms/Input/Select';
import { SelectOption } from '../../atoms/Input/SelectOption';
import { FormField } from '../../molecules/Form/FormField';

type DistributionType = 'uniform' | 'exponential' | 'normal' | 'gamma' | 'beta' | 'weibull' | 'lognormal' | 'binomial' | 'bernoulli' | 'poisson' | 'geometric' | 'hypergeometric';

type ColumnSetting = {
  id: string;
  column_name: string;
  data_type: 'distribution' | 'fixed';
  distribution_type?: DistributionType;
  distribution_params?: Record<string, number>;
  fixed_value?: string | number;
};

type ColumnConfigProps = {
  column: ColumnSetting;
  index: number;
  distributionOptions: Array<{ value: DistributionType; label: string; params: string[] }>;
  onUpdate: (id: string, updates: Partial<ColumnSetting>) => void;
  onDataTypeChange: (id: string, dataType: 'distribution' | 'fixed') => void;
  onDistributionTypeChange: (id: string, distributionType: DistributionType) => void;
  onDistributionParamChange: (id: string, param: string, value: number) => void;
  onRemove: (id: string) => void;
  canRemove: boolean;
};

export const ColumnConfig = ({
  column,
  index,
  distributionOptions,
  onUpdate,
  onDataTypeChange,
  onDistributionTypeChange,
  onDistributionParamChange,
  onRemove,
  canRemove
}: ColumnConfigProps) => {
  const { t } = useTranslation();
  const distOption = column.distribution_type ? distributionOptions.find(d => d.value === column.distribution_type) : null;

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
    <div className="border border-border-color dark:border-gray-700 rounded-lg p-4 bg-secondary-main dark:bg-gray-900/30">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        <div className="md:col-span-2 flex justify-between items-center">
          <p className="font-bold text-main dark:text-white">列 {index + 1}</p>
          <button
            onClick={() => onRemove(column.id)}
            className="text-gray-400 hover:text-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!canRemove}
          >
            <span className="material-symbols-outlined">delete</span>
          </button>
        </div>

        <FormField label={t('CreateSimulationDataTableView.ColumnName')} htmlFor={`column-name-${column.id}`}>
          <InputText
            id={`column-name-${column.id}`}
            value={column.column_name}
            change={(e) => onUpdate(column.id, { column_name: e.target.value })}
            placeholder="列名を入力"
          />
        </FormField>

        <FormField label={t('CreateSimulationDataTableView.DataType')} htmlFor={`data-type-${column.id}`}>
          <Select
            id={`data-type-${column.id}`}
            value={column.data_type}
            onChange={(e) => onDataTypeChange(column.id, e.target.value as 'distribution' | 'fixed')}
          >
            <SelectOption value="fixed">{t('Common.Constant')}</SelectOption>
            <SelectOption value="distribution">{t('Common.Distribution')}</SelectOption>
          </Select>
        </FormField>

        {column.data_type === 'distribution' && (
          <>
            <div className="md:col-span-2">
              <FormField label={t('CreateSimulationDataTableView.DistributionType')} htmlFor={`distribution-type-${column.id}`}>
                <Select
                  id={`distribution-type-${column.id}`}
                  value={column.distribution_type || ''}
                  onChange={(e) => onDistributionTypeChange(column.id, e.target.value as DistributionType)}
                >
                  {distributionOptions.map(option => (
                    <SelectOption key={option.value} value={option.value}>
                      {option.label}
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
                      value={column.distribution_params?.[param]?.toString() || ''}
                      change={(e) => onDistributionParamChange(column.id, param, parseFloat(e.target.value) || 0)}
                      placeholder={`${getParamLabel(param)}${t('CreateSimulationDataTableView.InputDistributionParameters')}`}
                    />
                  </FormField>
                ))}
              </div>
            )}
          </>
        )}

        {column.data_type === 'fixed' && (
          <div className="md:col-span-2 pt-2">
            <FormField label={t('CreateSimulationDataTableView.FixedValue')} htmlFor={`fixed-value-${column.id}`}>
              <InputText
                id={`fixed-value-${column.id}`}
                value={column.fixed_value?.toString() || ''}
                change={(e) => onUpdate(column.id, { fixed_value: e.target.value })}
                placeholder={t('CreateSimulationDataTableView.InputFixedValue')}
              />
            </FormField>
          </div>
        )}
      </div>
    </div>
  );
};
