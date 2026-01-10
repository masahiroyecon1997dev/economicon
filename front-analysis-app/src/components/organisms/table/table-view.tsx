import { Fragment } from "react/jsx-runtime";
import { getTableInfo } from "../../../function/internalFunctions";
import { useSettingsStore } from "../../../stores/useSettingsStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { MainTable } from "./main-table";
import { TableFooter } from "./table-footer";


export const TableView = () => {
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const updateTableInfo = useTableInfosStore((state) => state.updateTableInfo);
  const displayRows = useSettingsStore((state) => state.displayRows);


  const handlePageChange = async (tableName: string, page: number) => {
    const resTableInfo = await getTableInfo(
      tableName,
      (page - 1) * displayRows + 1,
      displayRows
    );
    updateTableInfo(tableName, resTableInfo);
  };

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
          <MainTable tableInfo={table}></MainTable>
          <TableFooter tableInfo={table} onPageChange={handlePageChange} />
        </Fragment>
      ))}
    </div>
  );
}
