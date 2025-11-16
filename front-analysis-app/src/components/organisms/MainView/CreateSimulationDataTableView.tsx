import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import axios from "../../../configs/axios";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useErrorDialogStore } from "../../../stores/useErrorDialogStore";
import { useLoadingStore } from "../../../stores/useLoadingStore";
import { CancelButton } from "../../atoms/Button/CancelButton";
import { SubmitButton } from "../../atoms/Button/SubmitButton";
import { InputText } from "../../atoms/Input/InputText";
import { FormField } from "../../molecules/Form/FormField";
import { ColumnConfig } from "../Form/ColumnConfig";

type DistributionType = 'uniform' | 'exponential' | 'normal' | 'gamma' | 'beta' | 'weibull' | 'lognormal' | 'binomial' | 'bernoulli' | 'poisson' | 'geometric' | 'hypergeometric';

type ColumnSetting = {
  id: string;
  column_name: string;
  data_type: 'distribution' | 'fixed';
  distribution_type?: DistributionType;
  distribution_params?: Record<string, number>;
  fixed_value?: string | number;
};

export const CreateSimulationDataTableView = () => {
  const { t } = useTranslation();
  const { setCurrentView } = useCurrentViewStore();
  const { showErrorDialog } = useErrorDialogStore();
  const { setLoading, clearLoading } = useLoadingStore();

  const DISTRIBUTION_OPTIONS: Array<{ value: DistributionType; label: string; params: string[] }> = [
    { value: 'uniform', label: t('Common.UniformDistribution'), params: ['low', 'high'] },
    { value: 'normal', label: t('Common.NomalDistribution'), params: ['loc', 'scale'] },
    { value: 'exponential', label: t('Common.ExponentialDistribution'), params: ['scale'] },
    { value: 'gamma', label: t('Common.GammaDistribution'), params: ['shape', 'scale'] },
    { value: 'beta', label: t('Common.BetaDistribution'), params: ['a', 'b'] },
    { value: 'weibull', label: t('Common.WeibullDistribution'), params: ['a'] },
    { value: 'lognormal', label: t('Common.LognormalDistribution'), params: ['mean', 'sigma'] },
    { value: 'binomial', label: t('Common.BinomialDistribution'), params: ['n', 'p'] },
    { value: 'bernoulli', label: t('Common.BernoulliDistribution'), params: ['p'] },
    { value: 'poisson', label: t('Common.PoissonDistribution'), params: ['lam'] },
    { value: 'geometric', label: t('Common.GeometricDistribution'), params: ['p'] },
    { value: 'hypergeometric', label: t('Common.HypergeometricDistribution'), params: ['K', 'N', 'n'] }
  ];

  const [tableName, setTableName] = useState('');
  const [numRows, setNumRows] = useState<number>(1000);
  const [columns, setColumns] = useState<ColumnSetting[]>([
    {
      id: '1',
      column_name: 'user_id',
      data_type: 'fixed',
      fixed_value: 1001
    }
  ]);
  const addColumn = () => {
    const newColumn: ColumnSetting = {
      id: Date.now().toString(),
      column_name: `column_${columns.length + 1}`,
      data_type: 'fixed',
      fixed_value: ''
    };
    setColumns([...columns, newColumn]);
  };

  const removeColumn = (id: string) => {
    setColumns(columns.filter(col => col.id !== id));
  };

  const updateColumn = (id: string, updates: Partial<ColumnSetting>) => {
    setColumns(columns.map(col =>
      col.id === id ? { ...col, ...updates } : col
    ));
  };

  const handleDataTypeChange = (id: string, dataType: 'distribution' | 'fixed') => {
    const updates: Partial<ColumnSetting> = {
      data_type: dataType,
    };

    if (dataType === 'distribution') {
      updates.distribution_type = 'uniform';
      updates.distribution_params = { low: 0, high: 10 };
      delete updates.fixed_value;
    } else {
      updates.fixed_value = '';
      delete updates.distribution_type;
      delete updates.distribution_params;
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
        case 'loc': defaultParams[param] = 0; break;
        case 'scale': defaultParams[param] = 1; break;
        case 'mean': defaultParams[param] = 0; break;
        case 'sigma': defaultParams[param] = 1; break;
        case 'shape': defaultParams[param] = 2; break;
        case 'a': defaultParams[param] = 1; break;
        case 'b': defaultParams[param] = 1; break;
        case 'n': defaultParams[param] = 10; break;
        case 'p': defaultParams[param] = 0.5; break;
        case 'lam': defaultParams[param] = 1; break;
        case 'K': defaultParams[param] = 5; break;
        case 'N': defaultParams[param] = 20; break;
        default: defaultParams[param] = 1;
      }
    });

    updateColumn(id, {
      distribution_type: distributionType,
      distribution_params: defaultParams
    });
  };

  const handleDistributionParamChange = (id: string, param: string, value: number) => {
    const column = columns.find(col => col.id === id);
    if (!column?.distribution_params) return;

    updateColumn(id, {
      distribution_params: {
        ...column.distribution_params,
        [param]: value
      }
    });
  };

  const validateForm = (): string | null => {
    if (!tableName.trim()) {
      return 'テーブル名を入力してください。';
    }

    if (numRows <= 0) {
      return '行数は1以上の整数を入力してください。';
    }

    if (columns.length === 0) {
      return '少なくとも1つの列を追加してください。';
    }

    for (const column of columns) {
      if (!column.column_name.trim()) {
        return 'すべての列に名前を入力してください。';
      }

      if (column.data_type === 'fixed' && (column.fixed_value === '' || column.fixed_value === undefined)) {
        return `列「${column.column_name}」の固定値を入力してください。`;
      }

      if (column.data_type === 'distribution' && !column.distribution_params) {
        return `列「${column.column_name}」の分布パラメータを設定してください。`;
      }
    }

    // 列名の重複チェック
    const columnNames = columns.map(col => col.column_name.trim());
    const duplicateNames = columnNames.filter((name, index) => columnNames.indexOf(name) !== index);
    if (duplicateNames.length > 0) {
      return `列名が重複しています: ${duplicateNames.join(', ')}`;
    }

    return null;
  };

  const handleSubmit = async () => {
    const validationError = validateForm();
    if (validationError) {
      await showErrorDialog('入力エラー', validationError);
      return;
    }

    setLoading(true, 'シミュレーションデータテーブルを作成中...');

    try {
      const columnSettings = columns.map(col => ({
        column_name: col.column_name.trim(),
        data_type: col.data_type,
        ...(col.data_type === 'distribution' ? {
          distribution_type: col.distribution_type,
          distribution_params: col.distribution_params
        } : {
          fixed_value: col.fixed_value
        })
      }));

      const response = await axios.post('/create-simulation-data-table', {
        tableName: tableName.trim(),
        tableNumberOfRows: numRows,
        columnSettings
      });

      if (response.data.code === 'OK') {
        setCurrentView('dataPreview');
      } else {
        await showErrorDialog('エラー', response.data.message || 'テーブルの作成に失敗しました。');
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
    <div className="mx-auto max-w-6xl">
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
              />
            </FormField>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800/50 p-6 rounded-lg border border-border-color dark:border-gray-700">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-main dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">列の設定</h2>
            <button
              onClick={addColumn}
              className="flex items-center gap-2 rounded-md bg-brand-primary text-white px-4 py-2 text-sm font-medium hover:bg-brand-primary-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-main"
            >
              <span className="material-symbols-outlined text-lg"><FontAwesomeIcon icon={faPlus} /></span>
              列を追加
            </button>
          </div>
          <div className="space-y-4">
            {columns.map((column, index) => (
              <ColumnConfig
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
