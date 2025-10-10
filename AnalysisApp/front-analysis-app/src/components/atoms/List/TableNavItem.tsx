import { FaAngleRight } from "react-icons/fa";

type TableNavItemProps = {
  tableName: string;
  isActive: boolean;
  onClick: (tableName: string) => void;
};

export function TableNavItem({ tableName, isActive, onClick }: TableNavItemProps) {
  return (
    <a
      className={`flex items-center justify-between rounded-md px-3 py-2 transition-colors cursor-pointer ${
        isActive
          ? "bg-gray-200 text-gray-900 font-medium"
          : "hover:bg-gray-100 text-gray-600 hover:text-gray-900"
      }`}
      onClick={() => onClick(tableName)}
    >
      <span>{tableName}</span>
      <FaAngleRight />
    </a>
  );
}
