import { Menu } from "lucide-react";
import { useTranslation } from "react-i18next";
import { showMessageDialog } from "../../lib/dialog/message";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useSideMenuStore } from "../../stores/sideMenu";
import { useTableInfosStore } from "../../stores/tableInfos";
import { SectionHeading } from "../atoms/List/SectionHeading";
import { TableNav } from "../molecules/List/TableNav";

export const LeftSideMenu = () => {
  const { t } = useTranslation();
  const isOpen = useSideMenuStore((state) => state.isOpen);
  const toggleSideMenu = useSideMenuStore((state) => state.toggleSideMenu);
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
    <aside
      className={`shrink-0 border-r border-brand-border bg-brand-primary text-white transition-all duration-300 ${isOpen ? "w-64" : "w-16"}`}
    >
      <div className="flex items-center p-4">
        <button
          onClick={toggleSideMenu}
          className={`p-2 rounded-md hover:bg-white/10 transition-colors ${isOpen ? "" : "mx-auto"}`}
          aria-label={
            isOpen ? t("Common.CloseSideMenu") : t("Common.OpenSideMenu")
          }
        >
          <Menu className="text-xl" size={20} />
        </button>
      </div>
      {isOpen && (
        <>
          <SectionHeading title={t("LeftSideMenu.Tables")} />
          <div className="px-4 pb-4">
            <TableNav
              activeTableName={activeTableName}
              onTableClick={clickTableName}
            />
          </div>
        </>
      )}
    </aside>
  );
};
