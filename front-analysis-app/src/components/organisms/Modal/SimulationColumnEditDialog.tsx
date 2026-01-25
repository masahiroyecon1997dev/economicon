import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { DistributionType, SimulationColumnSetting } from '../../../types/commonTypes';
import { Button } from '../../atoms/Button/Button';
import { SimulationColumnConfig } from '../Form/SimulationColumnConfig';

type SimulationColumnEditDialogProps = {
  isOpen: boolean;
  column: SimulationColumnSetting;
  index: number;
  distributionOptions: Array<{ value: DistributionType; label: string; params: string[] }>;
  onUpdate: (id: string, updates: Partial<SimulationColumnSetting>) => void;
  onDataTypeChange: (id: string, dataType: 'distribution' | 'fixed') => void;
  onDistributionTypeChange: (id: string, distributionType: DistributionType) => void;
  onDistributionParamChange: (id: string, param: string, value: number) => void;
  onRemove: (id: string) => void;
  onClose: () => void;
  canRemove: boolean;
  error: {
    columnName: string | undefined;
    distributionParams: Record<string, string | undefined> | undefined;
    fixedValue: string | undefined;
  };
  disabled?: boolean;
};

export const SimulationColumnEditDialog = ({
  isOpen,
  column,
  index,
  distributionOptions,
  onUpdate,
  onRemove,
  onClose,
  canRemove,
  error,
  disabled = false,
}: SimulationColumnEditDialogProps) => {
  const { t } = useTranslation();
  const [editingColumn, setEditingColumn] = useState<SimulationColumnSetting>(column);

  useEffect(() => {
    setEditingColumn(column);
  }, [column, isOpen]);

  const handleCancel = () => {
    setEditingColumn(column);
    onClose();
  };

  const handleSave = () => {
    if (!editingColumn.columnName || editingColumn.columnName.trim() === '') {
      return;
    }

    Object.keys(editingColumn).forEach(key => {
      if (key !== 'id' && key !== 'errorMessage') {
        const value = editingColumn[key as keyof SimulationColumnSetting];
        if (value !== column[key as keyof SimulationColumnSetting]) {
          onUpdate(column.id, { [key]: value });
        }
      }
    });
    onClose();
  };

  const handleLocalUpdate = (_id: string, updates: Partial<SimulationColumnSetting>) => {
    setEditingColumn(prev => ({ ...prev, ...updates }));
  };

  const handleLocalDataTypeChange = (_id: string, dataType: 'distribution' | 'fixed') => {
    const updates: Partial<SimulationColumnSetting> = {
      dataType: dataType,
    };

    if (dataType === 'distribution') {
      updates.distributionType = 'uniform';
      updates.distributionParams = { low: 0, high: 10 };
      updates.fixedValue = '';
    } else {
      updates.fixedValue = '';
      updates.distributionType = undefined;
      updates.distributionParams = undefined;
    }

    setEditingColumn(prev => ({ ...prev, ...updates }));
  };

  const handleLocalDistributionTypeChange = (_id: string, distributionType: DistributionType) => {
    const distOption = distributionOptions.find(d => d.value === distributionType);
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

    setEditingColumn(prev => ({
      ...prev,
      distributionType: distributionType,
      distributionParams: defaultParams
    }));
  };

  const handleLocalDistributionParamChange = (_id: string, param: string, value: number) => {
    setEditingColumn(prev => ({
      ...prev,
      distributionParams: {
        ...prev.distributionParams,
        [param]: value
      }
    }));
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => !open && handleCancel()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-gray-900/50 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl max-h-[85vh] -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white dark:bg-gray-800 shadow-lg data-[state=open]:animate-fade-in-down data-[state=closed]:animate-fade-out-up overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-b-gray-300 dark:border-b-gray-700 rounded-t">
            <Dialog.Title className="text-xl font-semibold text-gray-900 dark:text-white">
              {t('CreateSimulationDataTableView.EditColumn')} {index + 1}{t('Common.ColumnSuffix')}
            </Dialog.Title>
            <button
              type="button"
              onClick={handleCancel}
              className="text-gray-400 bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white rounded-lg text-sm w-8 h-8 inline-flex justify-center items-center"
              aria-label={t('Common.Close')}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <Dialog.Description asChild>
            <div className="p-4 md:p-5 overflow-y-auto max-h-[calc(85vh-160px)]">
              <SimulationColumnConfig
                column={editingColumn}
                index={index}
                distributionOptions={distributionOptions}
                onUpdate={handleLocalUpdate}
                onDataTypeChange={handleLocalDataTypeChange}
                onDistributionTypeChange={handleLocalDistributionTypeChange}
                onDistributionParamChange={handleLocalDistributionParamChange}
                onRemove={onRemove}
                canRemove={canRemove}
                error={error}
                disabled={disabled}
              />
            </div>
          </Dialog.Description>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 p-4 md:p-5 border-t border-gray-200 dark:border-gray-700 rounded-b">
            <Button onClick={handleCancel} variant="outline">
              {t('Common.Cancel')}
            </Button>
            <Button onClick={handleSave} variant="primary">
              {t('Common.Save')}
            </Button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
