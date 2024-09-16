import React, { useState, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";

import { SubmitButton } from "../../atoms/SubmitButton/SubmitButton";
import { Modal } from "../../molecules/Modal/Modal";
import { InputTextField } from "../../molecules/InputTextField/InputTextField";
import { InputText } from "../../atoms/InputText/InputText";

type SaveFileModalProps = {
  isGenerateSimulationDataModal: boolean;
  close: () => void;
};

export function GenerateDataModal({
  isGenerateSimulationDataModal,
  close,
}: SaveFileModalProps) {
  const { t } = useTranslation();
  const [tableName, setTableName] = useState<string>("");
  type tableDataSettingType = {
    columnName: string;
    coefficient: number;
    minValue: number;
    maxValue: number;
    error: string;
  };
  type tableDataSettingsType = tableDataSettingType[];
  const tableDataSettingsInitial = [
    { columnName: "col1", coefficient: 1, minValue: 0, maxValue: 1, error: "" },
  ];
  const [tableDataSettings, setTableDataSettings] =
    useState<tableDataSettingsType>(tableDataSettingsInitial);
  const [errorMean, setErrorMean] = useState<number>(0);
  const [errorVariance, setErrorVariance] = useState<number>(1);

  function changeTableName(event: ChangeEvent<HTMLInputElement>) {
    const tableName = event.target.value;
    setTableName(tableName);
  }

  function addColumn() {
    setTableDataSettings((preTableDataSettings) => [
      ...preTableDataSettings,
      {
        columnName: "col" + (preTableDataSettings.length + 1),
        coefficient: 1,
        minValue: 0,
        maxValue: 1,
        error: "",
      },
    ]);
  }

  function changeColumnName(event: ChangeEvent<HTMLInputElement>, num: number) {
    const columnName = event.target.value;
    setTableDataSettings((preTableDataSettings) =>
      preTableDataSettings.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, columnName: columnName };
        } else {
          return tableData;
        }
      })
    );
  }

  function changeMinValue(event: ChangeEvent<HTMLInputElement>, num: number) {
    const minValue = parseInt(event.target.value);
    setTableDataSettings((preTableDataSettings) =>
      preTableDataSettings.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, minValue: minValue };
        } else {
          return tableData;
        }
      })
    );
  }

  function changeMaxValue(event: ChangeEvent<HTMLInputElement>, num: number) {
    const maxValue = parseInt(event.target.value);
    setTableDataSettings((preTableDataSettings) =>
      preTableDataSettings.map((tableData, i) => {
        if (i === num) {
          return { ...tableData, maxValue: maxValue };
        } else {
          return tableData;
        }
      })
    );
  }

  function changeErrorMean(event: ChangeEvent<HTMLInputElement>) {
    const mean = parseInt(event.target.value);
    setErrorMean(mean);
  }

  function changeErrorVariance(event: ChangeEvent<HTMLInputElement>) {
    const variance = parseInt(event.target.value);
    setErrorVariance(variance);
  }

  async function generateFile() {}

  return (
    <Modal
      isOpenModal={isGenerateSimulationDataModal}
      modalTitle={t("GenerateDataModal.Title")}
      submitButtonName={t("GenerateDataModal.Generate")}
      submit={() => generateFile()}
      close={() => close()}
    >
      <InputTextField
        label={t("GenerateDataModal.TableName")}
        value={tableName}
        change={(event) => changeTableName(event)}
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
                  {t("GenerateDataModal.Min")}
                </th>
                <th className="p-5 text-left text-sm leading-6 font-semibold text-gray-900 capitalize">
                  {t("GenerateDataModal.Max")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-300">
              {tableDataSettings.map((column, i) => (
                <tr key={i}>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <InputText
                      value={column.columnName}
                      change={(event) => changeColumnName(event, i)}
                      error={t("")}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <input
                      type="number"
                      value={column.minValue}
                      onChange={(event) => changeMinValue(event, i)}
                    />
                  </td>
                  <td className="p-5 whitespace-nowrap text-sm leading-6 font-medium text-gray-900">
                    <input
                      type="number"
                      value={column.maxValue}
                      onChange={(event) => changeMaxValue(event, i)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="grid grid-cols-3 gap-4 leading-6">
          <div className="p-4 rounded-lg text-right text-lg content-center">
            {t("GenerateDataModal.ErrorMean")}
          </div>
          <div className="p-4 rounded-lg col-span-2">
            <input
              type="text"
              className="block w-full max-w-xs pr-4 py-2 text-sm font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none leading-relaxed"
              value={errorMean}
              onChange={(event) => changeErrorMean(event)}
            />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 leading-6">
          <div className="p-4 rounded-lg text-right text-lg content-center">
            {t("GenerateDataModal.ErrorVariance")}
          </div>
          <div className="p-4 rounded-lg col-span-2">
            <input
              type="text"
              className="block w-full max-w-xs pr-4 py-2 text-sm font-normal shadow-xs text-gray-900 bg-transparent border border-gray-300 rounded-lg placeholder-gray-400 focus:outline-none leading-relaxed"
              value={errorVariance}
              onChange={(event) => changeErrorVariance(event)}
            />
          </div>
        </div>
      </div>
    </Modal>
  );
}
