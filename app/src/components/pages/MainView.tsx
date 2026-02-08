import { useCurrentPageStore } from "../../stores/currentView";
import { Calculation } from "./Calculation";
import { CreateSimulationDataTable } from "./CreateSimulationDataTable";
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
  }

  return (
    <main className="flex-1 bg-brand-secondary overflow-auto h-full">
      <div className="p-8">
        {renderContent()}
      </div>
    </main>
  );
}
