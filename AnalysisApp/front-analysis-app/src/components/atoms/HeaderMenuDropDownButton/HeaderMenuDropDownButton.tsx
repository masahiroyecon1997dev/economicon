import React from 'react';

type HeaderMenuDropdownButtonProps = {
  children: string;
  clickEvent: () => void;
}

export function HeaderMenuDropdownButton({children, clickEvent}: HeaderMenuDropdownButtonProps) {
  return (
    <button className="block px-4 py-2 hover:bg-gray-200 w-full text-left" onClick={() => clickEvent()}>{children}</button>
  )
}
