import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { TableView } from "../Table/TableView";
import { RegressionFormView } from "./RegressionFormView";
import { SelectFileView } from "./SelectFileView";

export const MainView = () => {
  const currentView = useCurrentViewStore((state) => state.currentView);

  const renderContent = () => {
    switch (currentView) {
      case "selectFile":
        return <SelectFileView />;
      case "RegressionForm":
        return <RegressionFormView />;
      default:
        return <TableView />;
    }
  }

  return (
    <main className="flex-1 bg-brand-secondary p-8">
      {renderContent()}
    </main>
  );
}
