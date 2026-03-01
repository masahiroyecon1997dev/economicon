import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../lib/dialog/message";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { SectionHeading } from "../atoms/List/SectionHeading";
import { TableNav } from "../molecules/List/TableNav";

export const LeftSideMenu = () => {
  const { t } = useTranslation();
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const activateTableInfo = useTableInfosStore(
    (state) => state.activateTableInfo,
  );
  const setCurrentView = useCurrentPageStore((state) => state.setCurrentView);

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
      const message =
        error instanceof Error ? error.message : t("Error.UnexpectedError");
      await showMessageDialog(t("Error.Error"), message);
    }
  };

  return (
    <aside className="flex h-full w-full flex-col overflow-hidden bg-brand-primary dark:bg-gray-900 text-white">
      <SectionHeading title={t("LeftSideMenu.Tables")} />
      <div className="flex-1 overflow-y-auto px-4 pb-4">
        <TableNav
          activeTableName={activeTableName}
          onTableClick={clickTableName}
        />
      </div>
    </aside>
  );
};
