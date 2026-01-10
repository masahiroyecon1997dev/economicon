import { HelpCircle, Layers } from "lucide-react";
import { useTranslation } from "react-i18next";


import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { HeaderMenuDropdown } from "../../molecules/HeaderMenuDropdown/HeaderMenuDropdown";

export const HeaderMenu = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);

  const showCreateSimulationDataTableView = () => {
    setCurrentView("CreateSimulationDataTable");
  }

  const showLinearRegressionModal = () => {
    setCurrentView("LinearRegressionForm");
  }

  const showCalculationView = () => {
    setCurrentView("CalculationView");
  }

  const dataGenerationDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.DataGeneration"),
      dropdownListFunction: showCreateSimulationDataTableView,
    },
    {
      dropdownListName: t("HeaderMenu.Calculate"),
      dropdownListFunction: showCalculationView,
    },
  ];
  const addColumnDropdownListElement = [
    {
      dropdownListName: t("HeaderMenu.Calculate"),
      dropdownListFunction: showCalculationView,
    },
  ];
  const modelDropdownListElement = [
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
              <Layers size={24} />
            </div>
            <h1 className="text-xl font-bold">Data Analysis Tool</h1>
          </div>
          <div className="flex items-center gap-2">
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
              <HelpCircle size={20} />
            </div>
          </button>
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"></div>
        </div>
      </header>
    </>
  );
}
