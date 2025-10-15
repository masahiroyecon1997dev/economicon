import type { TableInfosType } from "../../../types/stateTypes";
import { MainTable } from "../Table/MainTable";
import { TableFooter } from "../Table/TableFooter";

type MainPanelProps = {
  tableInfos: TableInfosType;
};

export function MainPanel({ tableInfos }: MainPanelProps) {

  return (
    <main className="flex-1 overflow-y-auto bg-brand-secondary p-8">
      <div className="max-w-full mx-auto">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tableInfos.map((table, index) => (
              <a key={index} className="border-brand-primary text-brand-primary whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" href="#">{table.tableName}</a>
            ))}
          </nav>
        </div>
        {tableInfos.map((table, index) => (
          <MainTable key={index} tableInfo={table}></MainTable>
        ))}
        <TableFooter />
      </div>
    </main>
  );
}
