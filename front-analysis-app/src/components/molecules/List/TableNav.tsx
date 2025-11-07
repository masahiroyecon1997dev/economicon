import { useTableListStore } from "../../../stores/useTableListStore";
import { TableNavItem } from "../../atoms/List/TableNavItem";

type TableNavProps = {
  activeTableName: string | null;
  onTableClick: (tableName: string) => void;
};

export function TableNav({ activeTableName, onTableClick }: TableNavProps) {
  const tableList = useTableListStore((state) => state.tableList);

  return (
    <nav className="flex flex-col gap-1">
      {tableList.map((tableName, index) => (
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
