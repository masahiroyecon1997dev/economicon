import { useState } from "react";

import { ChevronDown } from "lucide-react";
import { cn } from "../../../common/utils";

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
      <button
        className={cn(
          "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
          "hover:bg-white/10 transition-colors"
        )}
        onClick={() => clickMenu()}
      >
        <span>{children}</span>
        <ChevronDown size={16} />
      </button>
      {openDropdown && (
        <div className="absolute left-0 mt-0 w-48 origin-top-left rounded-md bg-white shadow-lg focus:outline-none z-10">
          <div className="py-0">
            {dropdownListElement.map((item, i) => (
              <button
                className={cn(
                  "block w-full text-left px-4 py-2 text-sm text-gray-700",
                  "hover:bg-gray-100 cursor-pointer transition-colors",
                  i === 0 && "rounded-t-md",
                  i === dropdownListElement.length - 1 && "rounded-b-md"
                )}
                onClick={() => item.dropdownListFunction()}
              >
                {item.dropdownListName}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
