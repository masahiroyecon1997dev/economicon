import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { CalculationView } from "./CalculationView";
import { CreateSimulationDataTableView } from "./CreateSimulationDataTableView";
import { ImportDataFileView } from "./ImportDataFileView";
import { RegressionView } from "./RegressionView";
import { SaveDataView } from "./SaveDataView";
import { TableView } from "./TableView";

export const MainView = () => {
  const currentView = useCurrentViewStore((state) => state.currentView);

  const renderContent = () => {
    switch (currentView) {
      case "ImportDataFile":
        return <ImportDataFileView />;
      case "LinearRegressionForm":
        return <RegressionView />;
      case "CreateSimulationDataTable":
        return <CreateSimulationDataTableView />;
      case "CalculationView":
        return <CalculationView />;
      case "SaveData":
        return <SaveDataView />;
      default:
        return <TableView />;
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
