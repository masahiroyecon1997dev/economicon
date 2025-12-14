
import { faEllipsisVertical, faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";
import { DropdownMenu } from "../../molecules/Menu/DropdownMenu";
import { MenuItem } from "../Menu/MenuItem";
import { Tooltip } from "../Tooltip/Tooltip";

type TableNavItemProps = {
  tableName: string;
  isActive: boolean;
  onClick: (tableName: string) => void;
  onDelete?: (tableName: string) => void;
};

export const TableNavItem = ({ tableName, isActive, onClick, onDelete }: TableNavItemProps) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleMenuClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsMenuOpen(!isMenuOpen);
  };

  const handleDelete = () => {
    // e.stopPropagation();
    setIsMenuOpen(false);
    onDelete?.(tableName);
  };

  return (
    <Tooltip content={tableName} position="bottom">
      <div
        className={`flex items-center gap-2 rounded-md px-3 py-2 bg-white/20 text-white font-medium cursor-pointer ${isActive
          ? "bg-white/10 font-medium"
          : "hover:bg-white/10"
          }`}
        onClick={() => onClick(tableName)}
      >
        <div className="flex-1 min-w-0">
          <span className="block truncate">{tableName}</span>
        </div>
        <div className="relative">
          <button
            onClick={handleMenuClick}
            className="flex-shrink-0 p-1 rounded hover:bg-white/20 transition-colors"
            aria-label="テーブルメニュー"
          >
            <FontAwesomeIcon icon={faEllipsisVertical} />
          </button>
          <DropdownMenu
            isOpen={isMenuOpen}
            onClose={() => setIsMenuOpen(false)}
            position="bottom-right"
          >
            {onDelete && (
              <MenuItem
                icon={faTrash}
                label="削除"
                onClick={handleDelete}
                variant="danger"
              />
            )}
          </DropdownMenu>
        </div>
      </div>
    </Tooltip>
  );
}
