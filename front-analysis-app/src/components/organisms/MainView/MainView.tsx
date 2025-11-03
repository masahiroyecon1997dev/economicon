import type { CurrentViewType } from "../../../types/stateTypes";
import { SelectFileView } from "../SelectFile/SelectFileView";
import { TableView } from "../Table/TableView";

type MainViewProps = {
  currentView: CurrentViewType;
};

export function MainView({ currentView }: MainViewProps) {

  function renderContent() {
    switch (currentView) {
      case "selectFile":
        return <SelectFileView />;
      default:
        return <TableView />;
    }
  }

  return (
    <main className="flex-1 overflow-y-auto bg-brand-secondary p-8">
      {renderContent()}
    </main>
  );
}
