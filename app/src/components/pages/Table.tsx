import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/helpers";
import { useTableInfosStore } from "@/stores/tableInfos";
import { VirtualTable } from "@/components/organisms/Table/VirtualTable";

export const Table = () => {
  const { t } = useTranslation();
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );
  const removeTableInfo = useTableInfosStore((state) => state.removeTableInfo);

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* タブヘッダー */}
      <div className="border-b border-gray-200 shrink-0">
        <nav className="-mb-px flex space-x-1 overflow-x-auto">
          {tableInfos.map((table) => (
            <div
              role="button"
              tabIndex={0}
              key={table.tableName}
              onClick={() => activateTableInfo(table.tableName)}
              className={cn(
                "group whitespace-nowrap py-3 px-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5",
                table.isActive
                  ? "border-brand-primary text-brand-primary"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
              )}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  activateTableInfo(table.tableName);
                }
              }}
            >
              {table.tableName}
              <button
                type="button"
                aria-label={t("Table.CloseTab")}
                onClick={(e) => {
                  e.stopPropagation();
                  removeTableInfo(table.tableName);
                }}
                className={cn(
                  "rounded-full w-4 h-4 flex items-center justify-center transition-colors",
                  "opacity-0 group-hover:opacity-100 focus:opacity-100",
                  table.isActive
                    ? "hover:bg-brand-primary/20 text-brand-primary"
                    : "hover:bg-gray-200 text-gray-400 hover:text-gray-600",
                )}
              >
                <X className="w-2.5 h-2.5" />
              </button>
            </div>
          ))}
        </nav>
      </div>

      {/* テーブル本体: アクティブなテーブルのみマウント */}
      {tableInfos.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center text-brand-text-sub">
          <p className="text-sm">{t("Table.EmptyState")}</p>
        </div>
      )}
      {tableInfos.map(
        (table) =>
          table.isActive && (
            <div key={table.tableName} className="flex-1 min-h-0">
              <VirtualTable tableInfo={table} />
            </div>
          ),
      )}
    </div>
  );
};
