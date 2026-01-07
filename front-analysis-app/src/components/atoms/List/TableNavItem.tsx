
import { MoreVertical } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DropdownMenu } from "../../molecules/Menu/DropdownMenu";
import { MenuItem } from "../Menu/MenuItem";
import { Tooltip } from "../Tooltip/Tooltip";

type TableNavItemProps = {
  tableName: string;
  isActive: boolean;
  onClick: (tableName: string) => void;
};

export const TableNavItem = ({ tableName, isActive, onClick }: TableNavItemProps) => {
  const { t } = useTranslation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);


  const triggerButton = (
    <button
      className="shrink-0 p-1 rounded hover:bg-white/20 transition-colors"
      aria-label={t("AreaLabels.TableMenu")}
    >
      <MoreVertical size={16} />
    </button>
  );

  return (
    <div
      className={`flex items-center gap-2 rounded-md px-3 py-2 bg-white/20 text-white font-medium cursor-pointer ${isActive
        ? "bg-white/10 font-medium"
        : "hover:bg-white/10"
        }`}
      onClick={() => onClick(tableName)}
    >
      <Tooltip content={tableName} position="right" maxWidth={200}>
        <div className="flex-1 min-w-0">
          <span className="block truncate text-sm">{tableName}</span>
        </div>
      </Tooltip>
      <DropdownMenu
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        position="bottom-right"
        triggerElement={triggerButton}
      >
        <MenuItem
          label={t("LeftSideMenu.MenuDuplicateTable")}
          variant="default"
        />
        <MenuItem
          label={t("LeftSideMenu.MenuDeleteTable")}
          variant="default"
        />
      </DropdownMenu>
    </div>
  );
}
