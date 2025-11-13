import { useTranslation } from "react-i18next";
import { showErrorDialog } from "../../../function/errorDialog";
import { getTableInfo } from "../../../function/internalFunctions";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import { useTableInfosStore } from "../../../stores/useTableInfosStore";
import { SectionHeading } from "../../atoms/List/SectionHeading";
import { TableNav } from "../../molecules/List/TableNav";

export const LeftSideMenu = () => {
  const { t } = useTranslation();
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
      setCurrentView("dataPreview");
    } catch (error) {
      const message = error instanceof Error ? error.message : t('Error.UnexpectedError');
      await showErrorDialog(t("Error.Error"), message);
    }
  }

  return (
    <aside className="w-64 shrink-0 border-r border-brand-border bg-brand-primary p-4 text-white">
      <SectionHeading title={t("Common.Table")} />
      <TableNav
        activeTableName={activeTableName}
        onTableClick={clickTableName}
      />
    </aside>
  );
}
