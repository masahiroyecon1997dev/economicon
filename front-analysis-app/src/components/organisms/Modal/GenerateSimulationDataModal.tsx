import { useState, type ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { checkInteger, checkNumber, checkRequired } from '../../../function/checkInputFunctions';
import { getTableInfo } from '../../../function/internalFunctions';
import { generateSimulationData } from '../../../function/restApis';
import { useTableInfosStore } from '../../../stores/useTableInfosStore';
import type { ReqGenerateSimulationDataType } from '../../../types/apiTypes';
import { SubmitButton } from '../../atoms/Button/SubmitButton';
import { InputText } from '../../atoms/Input/InputText';
import { InputTextField } from '../../molecules/InputField/InputTextField';
import { Select } from '../../molecules/InputField/Select';
import { Modal } from '../../molecules/Modal/Modal';

type SaveFileModalProps = {
  isGenerateSimulationDataModal: boolean;
  close: () => void;
};

export function GenerateDataModal({
  isGenerateSimulationDataModal,
  close,
}: SaveFileModalProps) {
  const { t } = useTranslation();
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  type InputValueType = {
    tableName: string;
    tableNameError: string;
    numSamples: string;
    numSamplesError: string;
    columnData: {
      columnName: string;
      errorColumnName: string;
      dataType: string;
      errorDataType: string;
      value1: string;
      errorValue1: string;
      value2: string;
      errorValue2: string;
    }[];
  };

  const inputValueInitial: InputValueType = {
    tableName: '',
    tableNameError: '',
    numSamples: '1000',
    numSamplesError: '',
    columnData: [
      {
        columnName: 'col_1',
        errorColumnName: '',
        dataType: 'constant',
        errorDataType: '',
        value1: '0',
        errorValue1: '',
        value2: '1',
        errorValue2: '',
      },
    ],
  };

  const DATA_TYPE_LIST = [
    { value: 'constant', name: t('Common.Constant') },
    { value: 'uniform', name: t('Common.UniformDistribution') },
    { value: 'normal', name: t('Common.NomalDistribution') },
  ];

  const [inputValue, setInputValue] = useState<InputValueType>(inputValueInitial);

  function changeTableName(event: ChangeEvent<HTMLInputElement>) {
    const tableName = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      tableName: tableName,
    }));
  }

  function changenumSamples(event: ChangeEvent<HTMLInputElement>) {
    const numSamples = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      numSamples: numSamples,
    }));
  }

  function addColumn() {
    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: [
        ...preInputValue.columnData,
        {
          columnName: 'col_' + (preInputValue.columnData.length + 1),
          errorColumnName: '',
          dataType: 'constant',
          errorDataType: '',
          value1: '0',
          errorValue1: '',
          value2: '1',
          errorValue2: '',
        },
      ],
    }));
  }

  function changeColumnName(event: ChangeEvent<HTMLInputElement>, num: number) {
    const columnName = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, columnName: columnName };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeDataType(event: ChangeEvent<HTMLSelectElement>, num: number) {
    const dataType = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, dataType: dataType };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeValue1(event: ChangeEvent<HTMLInputElement>, num: number) {
    const value1 = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, value1: value1 };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeValue2(event: ChangeEvent<HTMLInputElement>, num: number) {
    const value2 = event.target.value;
    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, value2: value2 };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function checkInputValue(): boolean {
    let isError = false;
    const requiredTableName = checkRequired(inputValue.tableName);
    setInputValue(preInputValue => ({
      ...preInputValue,
      tableNameError: requiredTableName.message,
    }));
    isError = requiredTableName.isError || isError;
    const requirednumSamples = checkRequired(inputValue.numSamples);
    isError = requirednumSamples.isError || isError;
    if (!requirednumSamples.isError) {
      const integernumSamples = checkInteger(inputValue.numSamples);
      setInputValue(preInputValue => ({
        ...preInputValue,
        numSamplesError: integernumSamples.message,
      }));
      isError = integernumSamples.isError || isError;
    } else {
      setInputValue(preInputValue => ({
        ...preInputValue,
        numSamplesError: requirednumSamples.message,
      }));
    }

    setInputValue(preInputValue => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map(column => {
        const requiredColumnName = checkRequired(column.columnName);
        column.errorColumnName = requiredColumnName.message;
        isError = requiredColumnName.isError || isError;
        const requiredDataType = checkRequired(column.dataType);
        if (!requiredDataType.isError) {
          const numberDataType = checkNumber(column.dataType);
          column.errorDataType = numberDataType.message;
          isError = numberDataType.isError || isError;
        } else {
          column.errorDataType = requiredDataType.message;
          isError = requiredDataType.isError || isError;
        }
        const requiredValue1 = checkRequired(column.value1);
        if (!requiredValue1.isError) {
          const numberValue1 = checkNumber(column.value1);
          column.errorValue1 = numberValue1.message;
          isError = numberValue1.isError || isError;
        } else {
          column.errorValue1 = requiredValue1.message;
          isError = requiredValue1.isError || isError;
        }
        const requiredValue2 = checkRequired(column.value2);
        if (!requiredValue2.isError) {
          const numberValue2 = checkNumber(column.value2);
          column.errorValue2 = numberValue2.message;
          isError = numberValue2.isError || isError;
        } else {
          column.errorValue2 = requiredValue2.message;
          isError = requiredValue2.isError || isError;
        }
        return column;
      }),
    }));
    return isError;
  }

  async function generateData() {
    const isError = checkInputValue();
    if (isError) {
      return;
    }
    const dataStructure = [];
    for (const column of inputValue.columnData) {
      dataStructure.push({
        columnName: column.columnName,
        dataType: column.dataType,
        value1: Number(column.value1),
        value2: Number(column.value2),
      });
    }

    const reqGenerateSimulationData: ReqGenerateSimulationDataType = {
      tableName: inputValue.tableName,
      numSamples: Number(inputValue.numSamples),
      dataStructure: dataStructure,
    };
    const resGenerateSimulationData = await generateSimulationData(reqGenerateSimulationData);
    if (resGenerateSimulationData.code === 'OK') {
      const tableInfo = await getTableInfo(resGenerateSimulationData.result.tableName);
      addTableInfo(tableInfo);
      close();
    } else {
      window.alert(resGenerateSimulationData.message);
    }
  }

  return (
    <Modal
      isOpenModal={isGenerateSimulationDataModal}
      modalTitle={t('GenerateDataModal.Title')}
      submitButtonName={t('GenerateDataModal.Generate')}
      submit={() => generateData()}
      close={() => close()}
      modalSize="max-w-6xl"
    >
      <InputTextField
        label={t('GenerateDataModal.TableName')}
        value={inputValue.tableName}
        change={event => changeTableName(event)}
        error={inputValue.tableNameError}
      />
      <InputTextField
        label={t('GenerateDataModal.numSamples')}
        value={inputValue.numSamples}
        change={event => changenumSamples(event)}
        error={inputValue.numSamplesError}
      />
      <div className="p-4 overflow-hidden border-gray-300">
        <h3>{t('GenerateDataModal.Setting')}</h3>
        <SubmitButton submit={() => addColumn()}>{t('GenerateDataModal.AddColumn')}</SubmitButton>
        <div className="overflow-auto sm:max-h-40 md:max-h-48 lg:max-h-72 xl:max-h-80 2xl:max-h-96">
          <table className="min-w-full  rounded-xl">
            <thead>
              <tr>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t('GenerateDataModal.ColumnName')}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t('GenerateDataModal.DataType')}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t('GenerateDataModal.Min')}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t('GenerateDataModal.Max')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-300">
              {inputValue.columnData.map((column, i) => (
                <tr key={i}>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.columnName}
                      change={event => changeColumnName(event, i)}
                      error={column.errorColumnName}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <Select
                      optionList={DATA_TYPE_LIST}
                      selectFunc={event => changeDataType(event, i)}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.value1}
                      change={event => changeValue1(event, i)}
                      error={column.errorValue1}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.value2}
                      change={event => changeValue2(event, i)}
                      error={column.errorValue2}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Modal>
  );
}
