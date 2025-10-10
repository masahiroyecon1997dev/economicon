import { useState } from "react";

import { HeaderMenuButton } from "../../atoms/Button/HeaderMenuButton";
import { HeaderMenuDropdownButton } from "../../atoms/Button/HeaderMenuDropdownButton";

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
        <div className="absolute bg-brand-primary shadow-md z-50">
          {dropdownListElement.map((item, i) => (
            <HeaderMenuDropdownButton
              key={i}
              clickEvent={item.dropdownListFunction}
            >
              {item.dropdownListName}
            </HeaderMenuDropdownButton>
          ))}
        </div>
      )}
    </div>
  );
}
