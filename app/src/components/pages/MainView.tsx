import { useCurrentPageStore } from "../../stores/currentView";
import { Calculation } from "./Calculation";
import { CreateSimulationDataTable } from "./CreateSimulationDataTable";
import { CreateTable } from "./CreateTable";
import { ImportDataFile } from "./ImportDataFile";
import { Regression } from "./RegressionView";
import { SaveData } from "./SaveData";
import { Table } from "./Table";

export const MainView = () => {
  const currentView = useCurrentPageStore((state) => state.currentView);

  const renderContent = () => {
    switch (currentView) {
      case "ImportDataFile":
        return <ImportDataFile />;
      case "CreateTable":
        return <CreateTable />;
      case "LinearRegressionForm":
        return <Regression />;
      case "CreateSimulationDataTable":
        return <CreateSimulationDataTable />;
      case "CalculationView":
        return <Calculation />;
      case "SaveData":
        return <SaveData />;
      default:
        return <Table />;
    }
  };

  return (
    <main className="flex-1 flex flex-col overflow-hidden h-full bg-brand-secondary">
      <div
        className={
          currentView === "DataPreview"
            ? "flex-1 overflow-hidden p-4 flex flex-col min-h-0"
            : "flex-1 overflow-auto p-4"
        }
      >
        {renderContent()}
      </div>
    </main>
  );
};
