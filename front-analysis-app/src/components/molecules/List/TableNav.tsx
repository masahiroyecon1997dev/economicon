import type { TableNameListType } from "../../../types/stateTypes";
import { TableNavItem } from "../../atoms/List/TableNavItem";

type TableNavProps = {
  tableNameList: TableNameListType;
  activeTableName: string | null;
  onTableClick: (tableName: string) => void;
};

export function TableNav({ tableNameList, activeTableName, onTableClick }: TableNavProps) {
  return (
    <nav className="flex flex-col gap-1">
      {tableNameList.map((tableName, index) => (
        <TableNavItem
          key={index}
          tableName={tableName}
          isActive={activeTableName === tableName}
          onClick={onTableClick}
        />
      ))}
    </nav>
  );
}
