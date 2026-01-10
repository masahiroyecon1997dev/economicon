import { ChevronDown, HelpCircle, Layers } from "lucide-react";
import { useTranslation } from "react-i18next";


import { useState } from "react";
import { cn } from "../../../functions/utils";
import { useCurrentViewStore } from "../../../stores/useCurrentViewStore";
import type { DropmenuPositionType } from "../../../types/commonTypes";
import { MenuItem } from "../../atoms/Menu/MenuItem";
import { DropdownMenu } from "../../molecules/Menu/DropdownMenu";

const menuPosition: DropmenuPositionType = 'bottom';

export const HeaderMenu = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentViewStore((state) => state.setCurrentView);
  const [isDataMenuOpen, setIsDataMenuOpen] = useState(false);
  const [isRegressionMenuOpen, setIsRegressionMenuOpen] = useState(false);

  const dataMenuItems = [
    {
      id: 'data-generation',
      label: t("HeaderMenu.DataGeneration"),
      handleSelect: () => setCurrentView("CreateSimulationDataTable"),
    },
    {
      id: 'calculate',
      label: t("HeaderMenu.Calculate"),
      handleSelect: () => setCurrentView("CalculationView"),
    },
  ];
  const regressionMenuItems = [
    {
      id: 'linear-regression',
      label: t("HeaderMenu.LinearRegression"),
      handleSelect: () => setCurrentView("LinearRegressionForm"),
    }
  ];
  const menus = [
    { menuName: t('HeaderMenu.Data'), isOpen: isDataMenuOpen, onClose: () => setIsDataMenuOpen(false), position: menuPosition, items: dataMenuItems },
    { menuName: t('HeaderMenu.Model'), isOpen: isRegressionMenuOpen, onClose: () => setIsRegressionMenuOpen(false), position: menuPosition, items: regressionMenuItems },
  ]

  return (
    <>
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-brand-border bg-brand-primary px-6 text-white">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="size-6 text-white">
              <Layers size={24} />
            </div>
            <h1 className="text-xl font-bold">Data Analysis Tool</h1>
          </div>
          <div className="flex items-center gap-2">
            {menus.map((menu, index) => (
              <div key={index} className="relative group">
                <DropdownMenu
                  isOpen={menu.isOpen}
                  onClose={menu.onClose}
                  position={menu.position}
                  triggerElement={
                    <button
                      className={cn(
                        "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                        "hover:bg-white/10 transition-colors"
                      )}
                    >
                      <span>{menu.menuName}</span>
                      <ChevronDown size={16} />
                    </button>
                  }
                >
                  {menu.items.map((item, itemIndex) => (
                    <MenuItem
                      key={itemIndex}
                      label={item.label}
                      variant="default"
                      isFirst={itemIndex === 0}
                      isLast={itemIndex === menu.items.length - 1}
                      handleSelect={item.handleSelect} />
                  ))}
                </DropdownMenu>
              </div>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="rounded-full p-2 hover:bg-white/10 transition-colors">
            <div className="text-white">
              <HelpCircle size={20} />
            </div>
          </button>
          <div className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10"></div>
        </div>
      </header>
    </>
  );
}
