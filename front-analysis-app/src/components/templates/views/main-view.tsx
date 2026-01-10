import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { CalculationView } from "../../templates/views/calculation-view";
import { TableView } from "../Table/table-view";
import { CreateSimulationDataTableView } from "./create-simulation-data-table-view";
import { LinearRegressionFormView } from "./linear-regression-form-view";
import { SaveDataView } from "./save-data-view";
import { SelectFileView } from "./select-file-view";

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
