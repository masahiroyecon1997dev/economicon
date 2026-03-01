import { useTableInfosStore } from "../../stores/tableInfos";
import { VirtualTable } from "../organisms/Table/VirtualTable";

export const Table = () => {
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );

  return (
    <div className="max-w-full mx-auto">
      {/* タブヘッダー */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-1 overflow-x-auto">
          {tableInfos.map((table) => (
            <button
              key={table.tableName}
              onClick={() => activateTableInfo(table.tableName)}
              className={[
                "whitespace-nowrap py-3 px-4 text-sm font-medium border-b-2 transition-colors",
                table.isActive
                  ? "border-brand-primary text-brand-primary"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
              ].join(" ")}
            >
              {table.tableName}
            </button>
          ))}
        </nav>
      </div>

      {/* テーブル本体: 非アクティブは hidden でマウント保持 */}
      {tableInfos.map((table) => (
        <div
          key={table.tableName}
          className={table.isActive ? "block" : "hidden"}
        >
          <VirtualTable tableInfo={table} />
        </div>
      ))}
    </div>
  );
};
