import React, { useState, ChangeEvent, Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";

import { SubmitButton } from "../../atoms/SubmitButton/SubmitButton";
import { Modal } from "../../molecules/Modal/Modal";
import { InputTextField } from "../../molecules/InputTextField/InputTextField";
import { InputText } from "../../atoms/InputText/InputText";
import {
  checkInteger,
  checkNumber,
  checkRequired,
} from "../../../functiom/checkInputFunctions";
import { generateSimulationData } from "../../../functiom/restApis";
import { ReqGenerateSimulationDataType } from "../../../types/apiTypes";
import { getTableInfo } from "../../../functiom/internalFunctions";
import { TableInfosType } from "../../../types/stateTypes";

type SaveFileModalProps = {
  isGenerateSimulationDataModal: boolean;
  close: () => void;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
};

export function GenerateDataModal({
  isGenerateSimulationDataModal,
  close,
  setTableInfos,
}: SaveFileModalProps) {
  const { t } = useTranslation();
  type InputValueType = {
    tableName: string;
    tableNameError: string;
    numSamples: string;
    numSamplesError: string;
    columnData: {
      columnName: string;
      errorColumnName: string;
      coefficient: string;
      errorCoefficient: string;
      minValue: string;
      errorMinValue: string;
      maxValue: string;
      errorMaxValue: string;
    }[];
    errorMean: string;
    errorMeanError: string;
    errorVariance: string;
    errorVarianceError: string;
  };

  const inputValueInitial: InputValueType = {
    tableName: "",
    tableNameError: "",
    numSamples: "1000",
    numSamplesError: "",
    columnData: [
      {
        columnName: "col_1",
        errorColumnName: "",
        coefficient: "1",
        errorCoefficient: "",
        minValue: "0",
        errorMinValue: "",
        maxValue: "1",
        errorMaxValue: "",
      },
    ],
    errorMean: "0",
    errorMeanError: "",
    errorVariance: "1",
    errorVarianceError: "",
  };

  const [inputValue, setInputValue] =
    useState<InputValueType>(inputValueInitial);

  function changeTableName(event: ChangeEvent<HTMLInputElement>) {
    const tableName = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      tableName: tableName,
    }));
  }

  function changenumSamples(event: ChangeEvent<HTMLInputElement>) {
    const numSamples = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      numSamples: numSamples,
    }));
  }

  function addColumn() {
    setInputValue((preInputValue) => ({
      ...preInputValue,
      columnData: [
        ...preInputValue.columnData,
        {
          columnName: "col" + (preInputValue.columnData.length + 1),
          errorColumnName: "",
          coefficient: "1",
          errorCoefficient: "",
          minValue: "0",
          errorMinValue: "",
          maxValue: "1",
          errorMaxValue: "",
        },
      ],
    }));
  }

  function changeColumnName(event: ChangeEvent<HTMLInputElement>, num: number) {
    const columnName = event.target.value;
    setInputValue((preInputValue) => ({
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

  function changeCoefficient(
    event: ChangeEvent<HTMLInputElement>,
    num: number
  ) {
    const coefficient = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, coefficient: coefficient };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeMinValue(event: ChangeEvent<HTMLInputElement>, num: number) {
    const minValue = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, minValue: minValue };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeMaxValue(event: ChangeEvent<HTMLInputElement>, num: number) {
    const maxValue = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, maxValue: maxValue };
        } else {
          return tableData;
        }
      }),
    }));
  }

  function changeErrorMean(event: ChangeEvent<HTMLInputElement>) {
    const errorEmean = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      errorMean: errorEmean,
    }));
  }

  function changeErrorVariance(event: ChangeEvent<HTMLInputElement>) {
    const errorVariance = event.target.value;
    setInputValue((preInputValue) => ({
      ...preInputValue,
      errorVariance: errorVariance,
    }));
  }

  function checkInputValue(): boolean {
    let isError = false;
    const requiredTableName = checkRequired(inputValue.tableName);
    setInputValue((preInputValue) => ({
      ...preInputValue,
      tableNameError: requiredTableName.message,
    }));
    isError = requiredTableName.isError || isError;
    const requirednumSamples = checkRequired(inputValue.numSamples);
    isError = requirednumSamples.isError || isError;
    if (!requirednumSamples.isError) {
      const integernumSamples = checkInteger(inputValue.numSamples);
      setInputValue((preInputValue) => ({
        ...preInputValue,
        numSamplesError: integernumSamples.message,
      }));
      isError = integernumSamples.isError || isError;
    } else {
      setInputValue((preInputValue) => ({
        ...preInputValue,
        numSamplesError: requirednumSamples.message,
      }));
    }
    const requiredErrorMean = checkRequired(inputValue.errorMean);
    isError = requiredErrorMean.isError || isError;
    if (!requiredErrorMean.isError) {
      const numberErrorMean = checkNumber(inputValue.errorMean);
      setInputValue((preInputValue) => ({
        ...preInputValue,
        errorMeanError: numberErrorMean.message,
      }));
      isError = numberErrorMean.isError || isError;
    } else {
      setInputValue((preInputValue) => ({
        ...preInputValue,
        errorMeanError: requiredErrorMean.message,
      }));
    }
    const requiredErrorVariance = checkRequired(inputValue.errorVariance);
    isError = requiredErrorVariance.isError || isError;
    if (!requiredErrorVariance.isError) {
      const numberErrorVariance = checkNumber(inputValue.errorVariance);
      setInputValue((preInputValue) => ({
        ...preInputValue,
        errorVarianceError: numberErrorVariance.message,
      }));
      isError = numberErrorVariance.isError || isError;
    } else {
      setInputValue((preInputValue) => ({
        ...preInputValue,
        errorVarianceError: requiredErrorVariance.message,
      }));
    }

    setInputValue((preInputValue) => ({
      ...preInputValue,
      columnData: preInputValue.columnData.map((column, i) => {
        const requiredColumnName = checkRequired(column.columnName);
        column.errorColumnName = requiredColumnName.message;
        isError = requiredColumnName.isError || isError;
        const requiredCoefficient = checkRequired(column.coefficient);
        if (!requiredCoefficient.isError) {
          const numberCoefficient = checkNumber(column.coefficient);
          column.errorCoefficient = numberCoefficient.message;
          isError = numberCoefficient.isError || isError;
        } else {
          column.errorCoefficient = requiredCoefficient.message;
          requiredCoefficient.isError || isError;
        }
        const requiredMinValue = checkRequired(column.minValue);
        if (!requiredMinValue.isError) {
          const numberMinValue = checkNumber(column.minValue);
          column.errorMinValue = numberMinValue.message;
          isError = numberMinValue.isError || isError;
        } else {
          column.errorMinValue = requiredMinValue.message;
          isError = requiredMinValue.isError || isError;
        }
        const requiredMaxValue = checkRequired(column.maxValue);
        if (!requiredMaxValue.isError) {
          const numberMaxValue = checkNumber(column.maxValue);
          column.errorMaxValue = numberMaxValue.message;
          isError = numberMaxValue.isError || isError;
        } else {
          column.errorMaxValue = requiredMaxValue.message;
          isError = requiredMaxValue.isError || isError;
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
    let dataStructure = [];
    for (const column of inputValue.columnData) {
      dataStructure.push({
        columnName: column.columnName,
        coefficient: Number(column.coefficient),
        minValue: Number(column.minValue),
        maxValue: Number(column.maxValue),
      });
    }

    const reqGenerateSimulationData: ReqGenerateSimulationDataType = {
      tableName: inputValue.tableName,
      numSamples: Number(inputValue.numSamples),
      dataStructure: dataStructure,
      errorMean: Number(inputValue.errorMean),
      errorVariance: Number(inputValue.errorVariance),
    };
    const resGenerateSimulationData = await generateSimulationData(
      reqGenerateSimulationData
    );
    if (resGenerateSimulationData.code === 0) {
      const tableInfo = await getTableInfo(
        resGenerateSimulationData.result.tableName
      );
      console.log(tableInfo);
      setTableInfos((preTableInfos) => [tableInfo, ...preTableInfos]);
      close();
    } else {
      window.alert(resGenerateSimulationData.message);
    }
  }

  return (
    <Modal
      isOpenModal={isGenerateSimulationDataModal}
      modalTitle={t("GenerateDataModal.Title")}
      submitButtonName={t("GenerateDataModal.Generate")}
      submit={() => generateData()}
      close={() => close()}
    >
      <InputTextField
        label={t("GenerateDataModal.TableName")}
        value={inputValue.tableName}
        change={(event) => changeTableName(event)}
        error={inputValue.tableNameError}
      />
      <InputTextField
        label={t("GenerateDataModal.numSamples")}
        value={inputValue.numSamples}
        change={(event) => changenumSamples(event)}
        error={inputValue.numSamplesError}
      />
      <div className="p-4 overflow-hidden border-gray-300">
        <h3>{t("GenerateDataModal.Setting")}</h3>
        <SubmitButton submit={() => addColumn()}>
          {t("GenerateDataModal.AddColumn")}
        </SubmitButton>
        <div className="overflow-auto sm:max-h-40 md:max-h-48 lg:max-h-72 xl:max-h-80 2xl:max-h-96">
          <table className="min-w-full  rounded-xl">
            <thead>
              <tr>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t("GenerateDataModal.ColumnName")}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t("GenerateDataModal.Coefficient")}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t("GenerateDataModal.Min")}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t("GenerateDataModal.Max")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-300">
              {inputValue.columnData.map((column, i) => (
                <tr key={i}>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.columnName}
                      change={(event) => changeColumnName(event, i)}
                      error={column.errorColumnName}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.coefficient}
                      change={(event) => changeCoefficient(event, i)}
                      error={column.errorCoefficient}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.minValue}
                      change={(event) => changeMinValue(event, i)}
                      error={column.errorMinValue}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.maxValue}
                      change={(event) => changeMaxValue(event, i)}
                      error={column.errorMaxValue}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <InputTextField
        label={t("GenerateDataModal.ErrorMean")}
        value={inputValue.errorMean}
        change={(event) => changeErrorMean(event)}
        error={inputValue.errorMeanError}
      />
      <InputTextField
        label={t("GenerateDataModal.ErrorVariance")}
        value={inputValue.errorVariance}
        change={(event) => changeErrorVariance(event)}
        error={inputValue.errorVarianceError}
      />
    </Modal>
  );
}
