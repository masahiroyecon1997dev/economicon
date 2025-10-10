import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { TableInfosType } from "../../../types/stateTypes";

import { HeaderMenuDropdown } from "../../molecules/HeaderMenuDropdown/HeaderMenuDropdown";
import { Calculate } from "../Modal/Calculate";
import { GenerateDataModal } from "../Modal/GenerateSimulationDataModal";
import { ImportFileModal } from "../Modal/ImportFileModal";
import { LinearRegressionModal } from "../Modal/LinearRegressionModal";
import { SaveFileModal } from "../Modal/SaveFileModal";

type HeaderMenuProps = {
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
};

export function HeaderMenu({ setTableInfos }: HeaderMenuProps) {
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
  const addColumnDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.Calculate"),
      dropdownListFunction: openCalculateModal,
    },
  ];
  const modelDropdownListElement = [
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

  function openCalculateModal() {
    setIsCalculateModal(true);
  }

  function closeCalculateModal() {
    setIsCalculateModal(false);
  }

  return (
    <>
      <div className="flex bg-brand-primary text-white relative">
        <div className="flex items-center justify-center">
          <div className="text-lg font-bold italic">{t("HeaderMenu.Title")}</div>
        </div>
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
            dropdownListElement={addColumnDropdownListElement}
          >
            {t("HeaderMenu.AddColumn")}
          </HeaderMenuDropdown>
        </div>
        <div className="relative">
          <HeaderMenuDropdown dropdownListElement={modelDropdownListElement}>
            {t("HeaderMenu.Model")}
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
      />
      <SaveFileModal
        isSaveFileModal={isSaveFileModal}
        close={closeSaveFileModal}
      />
      <GenerateDataModal
        isGenerateSimulationDataModal={isGenerateSimulationDataModal}
        close={closeGenerateDataModal}
        setTableInfos={setTableInfos}
      />
      <Calculate
        isCalculateModal={isCalculateModal}
        close={closeCalculateModal}
      />
      <LinearRegressionModal
        isLinearRegressionModal={isLinearRegressionModal}
        close={closeLinearRegressionModal}
      />
    </>
  );
}
