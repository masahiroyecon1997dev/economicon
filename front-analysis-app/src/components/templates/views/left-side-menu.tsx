import { FileUp, Menu, Save } from "lucide-react";
import { useTranslation } from "react-i18next";
import { getTableInfo } from "../../../function/internalFunctions";
import { showMessageDialog } from "../../../function/messageDialog";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useSideMenuStore } from "../../../stores/useSideMenuStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { SectionHeading } from "../../atoms/List/section-heading";
import { TableNav } from "../../molecules/List/table-nav";

export const LeftSideMenu = () => {
  const { t } = useTranslation();
  const isOpen = useSideMenuStore((state) => state.isOpen);
  const toggleSideMenu = useSideMenuStore((state) => state.toggleSideMenu);
  const tableInfos = useTableInfosStore((state) => state.tableInfos);
  const activeTableName = useTableInfosStore((state) => state.activeTableName);
  const addTableInfo = useTableInfosStore((state) => state.addTableInfo);
  const activateTableInfo = useTableInfosStore((state) => state.activateTableInfo);
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);


  const clickTableName = async (tableName: string) => {
    try {
      const sameTableNameInfos = tableInfos.filter(
        (tableInfo) => tableInfo.tableName === tableName
      );
      if (sameTableNameInfos.length > 0) {
        activateTableInfo(tableName);
      } else {
        const tableInfo = await getTableInfo(tableName);
        addTableInfo(tableInfo);

      }
      setCurrentView("DataPreview");
    } catch (error) {
      const message = error instanceof Error ? error.message : t('Error.UnexpectedError');
      await showMessageDialog(t("Error.Error"), message);
    }
  }

  const showImportFileView = () => {
    setCurrentView("SelectFile");
  }

  const showSaveFileView = () => {
    setCurrentView("SaveData");
  }

  return (
    <aside className={`shrink-0 border-r border-brand-border bg-brand-primary text-white transition-all duration-300 ${isOpen ? 'w-64' : 'w-16'}`}>
      <div className="flex items-center p-4">
        <button
          onClick={toggleSideMenu}
          className={`p-2 rounded-md hover:bg-white/10 transition-colors ${isOpen ? '' : 'mx-auto'}`}
          aria-label={isOpen ? t("Common.CloseSideMenu") : t("Common.OpenSideMenu")}
        >
          <Menu className="text-xl" size={20} />
        </button>
      </div>
      {isOpen && (
        <>
          <div className="px-4 pb-2 space-y-2">
            <button
              onClick={showImportFileView}
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-left hover:cursor-pointer"
            >
              <FileUp className="text-lg" size={18} />
              <span className="font-medium">{t("LeftSideMenu.ImportData")}</span>
            </button>
            <button
              onClick={showSaveFileView}
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-white/10 transition-colors text-left hover:cursor-pointer"
            >
              <Save className="text-lg" size={18} />
              <span className="font-medium">{t("LeftSideMenu.SaveData")}</span>
            </button>
          </div>
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
}
