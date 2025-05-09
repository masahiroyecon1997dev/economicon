import React, { useState, Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";

import { TableInfosType, TableListType } from "../../../types/stateTypes";

import { HeaderMenuDropdown } from "../../molecules/HeaderMenuDropdown/HeaderMenuDropdown";
import { ImportFileModal } from "../ImportFileModal/ImportFileModal";
import { SaveFileModal } from "../SaveFileModal/SaveFileModal";
import { GenerateDataModal } from "../GenerateSimulationDataModal/GenerateSimulationDataModal";
import { LinearRegressionModal } from "../LinearRegressionModal/LinearRegressionModal";

type HeaderMenuProps = {
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
  setTableList: Dispatch<SetStateAction<TableListType>>;
};

export function HeaderMenu({ setTableInfos, setTableList }: HeaderMenuProps) {
  const { t } = useTranslation();
  const [isImportFileModal, setIsImportFileModal] = useState<boolean>(false);
  const [isSaveFileModal, setIsSaveFileModal] = useState<boolean>(false);
  const [isGenerateSimulationDataModal, setGenerateSimulationDataModal] =
    useState<boolean>(false);
  const [isLinearRegressionModal, setIsLinearRegressionModal] =
    useState<boolean>(false);
  const [isCalculateModal, setIsCalculateModal] = useState<boolean>(false);

  const fileDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.FileOpen"),
      dropdownListFunction: openImportFileModal,
    },
    {
      dropdownListName: t("HeaderMenu.FileSave"),
      dropdownListFunction: openSaveFileModal,
    },
  ];
  const dataGenerationDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.DataGeneration"),
      dropdownListFunction: openGenerateDataModal,
    },
    {
      dropdownListName: t("HeaderMenu.SampleData"),
      dropdownListFunction: openImportFileModal,
    },
  ];
  const linearRegressionDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.LinearRegression"),
      dropdownListFunction: openLinearRegressionModal,
    },
    // {
    //   dropdownListName: t("HeaderMenu.LogitAnalysis"),
    //   dropdownListFunction:
    // },
  ];

  function openImportFileModal() {
    setIsImportFileModal(true);
  }

  function closeImportFileModal() {
    setIsImportFileModal(false);
  }

  function openSaveFileModal() {
    setIsSaveFileModal(true);
  }

  function closeSaveFileModal() {
    setIsSaveFileModal(false);
  }

  function openGenerateDataModal() {
    setGenerateSimulationDataModal(true);
  }

  function closeGenerateDataModal() {
    setGenerateSimulationDataModal(false);
  }

  function openLinearRegressionModal() {
    setIsLinearRegressionModal(true);
  }

  function closeLinearRegressionModal() {
    setIsLinearRegressionModal(false);
  }

  return (
    <>
      <div className="flex bg-gray-100 border-b border-gray-300 relative">
        <div className="relative">
          <HeaderMenuDropdown dropdownListElement={fileDropdownListElement}>
            {t("HeaderMenu.File")}
          </HeaderMenuDropdown>
        </div>
        <div className="relative">
          <HeaderMenuDropdown
            dropdownListElement={dataGenerationDropdownListElement}
          >
            {t("HeaderMenu.Data")}
          </HeaderMenuDropdown>
        </div>
        <div className="relative">
          <HeaderMenuDropdown
            dropdownListElement={linearRegressionDropdownListElement}
          >
            {t("HeaderMenu.RegressionAnalysis")}
          </HeaderMenuDropdown>
        </div>
        {/* <button className="px-4 py-2 hover:bg-gray-200">編集</button>
        <button className="px-4 py-2 hover:bg-gray-200">表示</button>
        <button className="px-4 py-2 hover:bg-gray-200">挿入</button>
        <button className="px-4 py-2 hover:bg-gray-200">書式</button>
        <button className="px-4 py-2 hover:bg-gray-200">データ</button>
        <button className="px-4 py-2 hover:bg-gray-200">ツール</button>
        <button className="px-4 py-2 hover:bg-gray-200">ヘルプ</button> */}
      </div>
      <ImportFileModal
        isImportFileModal={isImportFileModal}
        close={closeImportFileModal}
        setTableInfos={setTableInfos}
        setTableList={setTableList}
      />
      <SaveFileModal
        isSaveFileModal={isSaveFileModal}
        close={closeSaveFileModal}
      />
      <GenerateDataModal
        isGenerateSimulationDataModal={isGenerateSimulationDataModal}
        close={closeGenerateDataModal}
        setTableInfos={setTableInfos}
        setTableList={setTableList}
      />
      <LinearRegressionModal
        isLinearRegressionModal={isLinearRegressionModal}
        close={closeLinearRegressionModal}
      />
    </>
  );
}
