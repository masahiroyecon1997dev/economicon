import { useState } from "react";

import { HeaderMenuButton } from "../../atoms/Button/header-menu-button";
import { HeaderMenuDropdownButton } from "../../atoms/Button/header-menu-dropdown-button";

type HeaderMenuDropdownProps = {
  children: string;
  dropdownListElement: {
    dropdownListName: string;
    dropdownListFunction: () => void;
  }[];
};

export function HeaderMenuDropdown({
  children,
  dropdownListElement,
}: HeaderMenuDropdownProps) {
  const [openDropdown, setOpenDropdown] = useState<boolean>(false);

  function clickMenu() {
    setOpenDropdown((preOpenDropdown) => !preOpenDropdown);
  }

  function onMouseEvent() {
    setOpenDropdown(true);
  }

  function leaveMouseEvent() {
    setOpenDropdown(false);
  }

  return (
    <div
      onMouseEnter={() => onMouseEvent()}
      onMouseLeave={() => leaveMouseEvent()}
    >
      <HeaderMenuButton clickEvent={() => clickMenu()}>
        {children}
      </HeaderMenuButton>
      {openDropdown && (
        <div className="absolute left-0 mt-0 w-48 origin-top-left rounded-md bg-white shadow-lg focus:outline-none z-10">
          <div className="py-0">
            {dropdownListElement.map((item, i) => (
              <HeaderMenuDropdownButton
                key={i}
                isTop={i === 0}
                isBottom={i === dropdownListElement.length - 1}
                clickEvent={item.dropdownListFunction}
              >
                {item.dropdownListName}
              </HeaderMenuDropdownButton>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
