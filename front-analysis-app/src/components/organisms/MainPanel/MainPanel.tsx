import type { CurrentViewType, TableInfosType } from "../../../types/stateTypes";
import { TablePanel } from "../Table/TableView";

type MainPanelProps = {
  tableInfos: TableInfosType;
  currentView: CurrentViewType;
};

export function MainPanel({ tableInfos, currentView }: MainPanelProps) {

  return (
    <main className="flex-1 overflow-y-auto bg-brand-secondary p-8">
      {isImportFileByPathView ? (
        <div>
          {/* Import file by path view content goes here */}
        </div>
      ) : (
        <TablePanel tableInfos={tableInfos} />
      )}
    </main>
  );
}
