import type { TableInfosType } from "../../../types/stateTypes";
import { TableNavItem } from "../../atoms/List/TableNavItem";

type TableNavProps = {
  tableInfos: TableInfosType;
  activeTableName: string | null;
  onTableClick: (tableName: string) => void;
};

export function TableNav({ tableInfos, activeTableName, onTableClick }: TableNavProps) {
  return (
    <nav className="flex flex-col gap-1">
      {tableInfos.map((info, index) => (
        <TableNavItem
          key={index}
          tableName={info.tableName}
          isActive={activeTableName === info.tableName}
          onClick={onTableClick}
        />
      ))}
    </nav>
  );
}
