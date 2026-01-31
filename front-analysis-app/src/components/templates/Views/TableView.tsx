import { Fragment } from "react/jsx-runtime";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { VirtualTable } from "../../organisms/Table/VirtualTable";


export const TableView = () => {
  const tableInfos = useTableInfosStore((state) => state.tableInfos);

  return (
    <div className="max-w-full mx-auto">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tableInfos.map((table, index) => (
            <a key={index} className="border-brand-primary text-brand-primary whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm" href="#">{table.tableName}</a>
          ))}
        </nav>
      </div>
      {tableInfos.map((table, index) => (
        <Fragment key={index}>
          <VirtualTable tableInfo={table} />
        </Fragment>
      ))}
    </div>
  );
}
