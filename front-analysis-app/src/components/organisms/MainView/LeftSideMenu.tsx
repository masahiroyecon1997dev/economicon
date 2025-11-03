import { useTranslation } from "react-i18next";
import { getTableInfo } from "../../../function/internalFunctions";
import addTableInfosStore from "../../../stores/useTableInfosStore";
import { SectionHeading } from "../../atoms/List/SectionHeading";
import { TableNav } from "../../molecules/List/TableNav";

export function LeftSideMenu() {
  const { t } = useTranslation();
  const addTableInfos = addTableInfosStore((state) => state.addTableInfo);
  const activateTableInfos = addTableInfosStore((state) => state.activateTableInfo);
  const tableInfos = addTableInfosStore((state) => state.tableInfos);


  async function clickTableName(tableName: string) {
    const sameTableNameInfos = tableInfos.filter(
      (tableInfo) => tableInfo.tableName === tableName
    );
    if (sameTableNameInfos.length > 0) {
      activateTableInfos(tableName);
    } else {
      const tableInfo = await getTableInfo(tableName);
      addTableInfos(tableInfo);
    }
  }

  const getActiveTableName = () => {
    const activeTable = tableInfos.find((tableInfo) => tableInfo.isActive);
    return activeTable?.tableName || null;
  };

  const activeTableName = getActiveTableName();

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
