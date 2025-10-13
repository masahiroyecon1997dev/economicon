import type { Dispatch, SetStateAction } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconContext } from "react-icons";
import { AiOutlineQuestionCircle } from "react-icons/ai";
import { LuLayers3 } from "react-icons/lu";

import type { TableInfosType, TableNameListType } from "../../../types/stateTypes";

import { HeaderMenuDropdown } from "../../molecules/HeaderMenuDropdown/HeaderMenuDropdown";
import { Calculate } from "../Modal/Calculate";
import { GenerateDataModal } from "../Modal/GenerateSimulationDataModal";
import { ImportFileModal } from "../Modal/ImportFileModal";
import { LinearRegressionModal } from "../Modal/LinearRegressionModal";
import { SaveFileModal } from "../Modal/SaveFileModal";

type HeaderMenuProps = {
  setTableNameList: Dispatch<SetStateAction<TableNameListType>>;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
};

export function HeaderMenu({ setTableNameList, setTableInfos }: HeaderMenuProps) {
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
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-brand-border-color bg-brand-primary px-6 text-white">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="size-6 text-white">
              <IconContext.Provider value={{ size: '1.5rem'}}>
                <LuLayers3 />
              </IconContext.Provider>
            </div>
            <h1 className="text-xl font-bold italic">{t("HeaderMenu.Title")}</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative group">
              <HeaderMenuDropdown dropdownListElement={fileDropdownListElement}>
                {t("HeaderMenu.File")}
              </HeaderMenuDropdown>
            </div>
            <div className="relative group">
              <HeaderMenuDropdown
                dropdownListElement={dataGenerationDropdownListElement}
              >
                {t("HeaderMenu.Data")}
              </HeaderMenuDropdown>
            </div>
            <div className="relative group">
              <HeaderMenuDropdown
                dropdownListElement={addColumnDropdownListElement}
              >
                {t("HeaderMenu.AddColumn")}
              </HeaderMenuDropdown>
            </div>
            <div className="relative group">
              <HeaderMenuDropdown dropdownListElement={modelDropdownListElement}>
                {t("HeaderMenu.Model")}
              </HeaderMenuDropdown>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="rounded-full p-2 hover:bg-white/10 transition-colors">
            <div className="text-white">
              <IconContext.Provider value={{ size: '1.5rem' }}>
                <AiOutlineQuestionCircle />
              </IconContext.Provider>
            </div>
          </button>
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"></div>
        </div>
      </header>
      <ImportFileModal
        isImportFileModal={isImportFileModal}
        close={closeImportFileModal}
        setTableNameList={setTableNameList}
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
