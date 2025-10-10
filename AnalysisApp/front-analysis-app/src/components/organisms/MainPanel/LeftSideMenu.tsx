import type { Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";
import { getTableInfo } from "../../../function/internalFunctions";
import type { TableInfosType } from "../../../types/stateTypes";
import { SectionHeading } from "../../atoms/List/SectionHeading";
import { TableNav } from "../../molecules/List/TableNav";

type LeftSideMenuProps = {
  tableInfos: TableInfosType;
  setTableInfos: Dispatch<SetStateAction<TableInfosType>>;
};

export function LeftSideMenu({
  tableInfos,
  setTableInfos
}: LeftSideMenuProps) {
  const { t } = useTranslation();

  async function clickTableName(tableName: string) {
    const sameTableNameInfos = tableInfos.filter(
      (tableInfo) => tableInfo.tableName === tableName
    );
    if (sameTableNameInfos.length > 0) {
      setTableInfos((preTableInfos) =>
        preTableInfos.map((tableInfo) => {
          if (tableInfo.tableName === tableName) {
            return { ...tableInfo, isActive: true };
          } else {
            return { ...tableInfo, isActive: false };
          }
        })
      );
    } else {
      const tableInfo = await getTableInfo(tableName);
      setTableInfos((preTableInfos) => [
        ...preTableInfos.map((info) => ({ ...info, isActive: false })),
        tableInfo,
      ]);
    }
  }

  const getActiveTableName = () => {
    const activeTable = tableInfos.find((tableInfo) => tableInfo.isActive);
    return activeTable?.tableName || null;
  };

  const activeTableName = getActiveTableName();

  return (
    <div className="flex flex-1 overflow-hidden">
      <aside className="w-64 shrink-0 border-r border-brand-border-color bg-gray-50 p-4">
        <SectionHeading title={t("Common.Table")} />
        <TableNav
          tableInfos={tableInfos}
          activeTableName={activeTableName}
          onTableClick={clickTableName}
        />
      </aside>
    </div>
  );
}
