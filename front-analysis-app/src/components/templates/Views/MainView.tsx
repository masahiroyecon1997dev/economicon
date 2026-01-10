import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { CalculationView } from "./CalculationView";
import { CreateSimulationDataTableView } from "./CreateSimulationDataTableView";
import { LinearRegressionFormView } from "./LinearRegressionFormView";
import { SaveDataView } from "./SaveDataView";
import { SelectFileView } from "./SelectFileView";
import { TableView } from "./TableView";

export const MainView = () => {
  const currentView = useCurrentViewStore((state) => state.currentView);

  const renderContent = () => {
    switch (currentView) {
      case "SelectFile":
        return <SelectFileView />;
      case "LinearRegressionForm":
        return <LinearRegressionFormView />;
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
