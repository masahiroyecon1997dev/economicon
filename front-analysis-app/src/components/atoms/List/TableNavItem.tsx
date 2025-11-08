
import { faAngleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type TableNavItemProps = {
  tableName: string;
  isActive: boolean;
  onClick: (tableName: string) => void;
};

export const TableNavItem = ({ tableName, isActive, onClick }: TableNavItemProps) => {
  return (
    <a
      className={`flex items-center justify-between rounded-md px-3 py-2 bg-white/20 text-white font-medium cursor-pointer ${isActive
          ? "bg-white/10 font-medium"
          : "hover:bg-white/10"
        }`}
      onClick={() => onClick(tableName)}
    >
      <span>{tableName}</span>
      <FontAwesomeIcon icon={faAngleRight} />
    </a>
  );
}
