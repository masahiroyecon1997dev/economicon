import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { SelectFileView } from "../SelectFile/SelectFileView";
import { TableView } from "../Table/TableView";

export const MainView = () => {
  const currentView = useCurrentViewStore((state) => state.currentView);

  const renderContent = () => {
    switch (currentView) {
      case "selectFile":
        return <SelectFileView />;
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
