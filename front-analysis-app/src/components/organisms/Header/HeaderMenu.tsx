import { faCircleQuestion } from "@fortawesome/free-regular-svg-icons";
import { faLayerGroup } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { useTranslation } from "react-i18next";


import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { HeaderMenuDropdown } from "../../molecules/HeaderMenuDropdown/HeaderMenuDropdown";
import { Calculate } from "../Modal/Calculate";
import { GenerateDataModal } from "../Modal/GenerateSimulationDataModal";
import { ImportFileModal } from "../Modal/ImportFileModal";
import { LinearRegressionModal } from "../Modal/LinearRegressionModal";
import { SaveFileModal } from "../Modal/SaveFileModal";

export const HeaderMenu = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
  const [isImportFileByUploadModal, setIsImportFileByUploadModal] = useState<boolean>(false);
  const [isSaveFileModal, setIsSaveFileModal] = useState<boolean>(false);
  const [isGenerateSimulationDataModal, setGenerateSimulationDataModal] =
    useState<boolean>(false);
  const [isLinearRegressionModal, setIsLinearRegressionModal] =
    useState<boolean>(false);
  const [isCalculateModal, setIsCalculateModal] = useState<boolean>(false);

  const showImportFileByPathView = () => {
    setCurrentView("selectFile");
  }

  const showCreateSimulationDataTableView = () => {
    setCurrentView("CreateSimulationDataTable");
  }

  const showLinearRegressionModal = () => {
    setCurrentView("LinearRegressionForm");
  }

  const openImportFileByUploadModal = () => {
    setIsImportFileByUploadModal(true);
  }

  const closeImportFileByUploadModal = () => {
    setIsImportFileByUploadModal(false);
  }

  const openSaveFileModal = () => {
    setIsSaveFileModal(true);
  }

  const closeSaveFileModal = () => {
    setIsSaveFileModal(false);
  }

  const openGenerateDataModal = () => {
    setGenerateSimulationDataModal(true);
  }

  const closeGenerateDataModal = () => {
    setGenerateSimulationDataModal(false);
  }

  const openLinearRegressionModal = () => {
    setIsLinearRegressionModal(true);
  }



  const closeLinearRegressionModal = () => {
    setIsLinearRegressionModal(false);
  }

  const openCalculateModal = () => {
    setIsCalculateModal(true);
  }

  const closeCalculateModal = () => {
    setIsCalculateModal(false);
  }

  const fileDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.FileOpen"),
      dropdownListFunction: showImportFileByPathView,
    },
    {
      dropdownListName: t("HeaderMenu.UploadFile"),
      dropdownListFunction: openImportFileByUploadModal,
    },
    {
      dropdownListName: t("HeaderMenu.FileSave"),
      dropdownListFunction: openSaveFileModal,
    },
  ];
  const dataGenerationDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.DataGeneration"),
      dropdownListFunction: showCreateSimulationDataTableView,
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
    {
      dropdownListName: t("HeaderMenu.LinearRegression"),
      dropdownListFunction: showLinearRegressionModal,
    }
  ];

  return (
    <>
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-brand-border bg-brand-primary px-6 text-white">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="size-6 text-white">
              <FontAwesomeIcon icon={faLayerGroup} />
            </div>
            <h1 className="text-xl font-bold">Data Analysis Tool</h1>
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
              <FontAwesomeIcon icon={faCircleQuestion} />
            </div>
          </button>
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"></div>
        </div>
      </header>
      <ImportFileModal
        isImportFileModal={isImportFileByUploadModal}
        close={closeImportFileByUploadModal}
      />
      <SaveFileModal
        isSaveFileModal={isSaveFileModal}
        close={closeSaveFileModal}
      />
      <GenerateDataModal
        isGenerateSimulationDataModal={isGenerateSimulationDataModal}
        close={closeGenerateDataModal}
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
