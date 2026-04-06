import { useTranslation } from "react-i18next";
import { showMessageDialog } from "@/lib/dialog/message";
import { extractApiErrorMessage } from "@/lib/utils/apiError";
import { getTableInfo } from "@/lib/utils/internal";
import { useCurrentPageStore } from "@/stores/currentView";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useTableListStore } from "@/stores/tableList";
import { SectionHeading } from "@/components/atoms/List/SectionHeading";
import { TableNav } from "@/components/molecules/List/TableNav";

export const LeftSideMenu = () => {
  const { t } = useTranslation();
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);
  const tableList = useTableListStore((state) => state.tableList);

  const clickTableName = async (tableName: string) => {
    try {
      const sameTableNameInfos = tableInfos.filter(
        (tableInfo) => tableInfo.tableName === tableName,
      );
      if (sameTableNameInfos.length > 0) {
        activateTableInfo(tableName);
      } else {
        const tableInfo = await getTableInfo(tableName);
        addTableInfo(tableInfo);
      }
      setCurrentView("DataPreview");
    } catch (error) {
      await showMessageDialog(
        t("Error.Error"),
        extractApiErrorMessage(error, t("Error.UnexpectedError")),
      );
    }
  };

  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-brand-primary dark:bg-gray-900 text-white">
      <SectionHeading title={t("LeftSideMenu.DataList")} />
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {tableList.length === 0 && (
          <p className="mt-2 text-xs text-white/40 leading-relaxed whitespace-pre-line">
            {t("LeftSideMenu.EmptyState")}
          </p>
        )}
        <TableNav
          activeTableName={activeTableName}
          onTableClick={clickTableName}
        />
      </div>
    </aside>
  );
};
