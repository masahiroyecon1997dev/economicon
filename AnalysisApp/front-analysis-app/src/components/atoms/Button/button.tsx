import React from 'react';

type HeaderMenuButtonProps = {
  children: string;
  clickEvent: () => void;
}

export function HeaderMenuButton({children, clickEvent}: HeaderMenuButtonProps) {
  return (
    <button className="px-4 py-2 hover:bg-gray-200" onClick={() => clickEvent()}>{children}</button>
  );
}

type HeaderMenuDropDownButtonProps = {
  children: string;
  clickEvent: () => void;
}

export function HeaderMenuDropDownButton({children, clickEvent}: HeaderMenuDropDownButtonProps) {
  return (
    <button className="block px-4 py-2 hover:bg-gray-200 w-full text-left" onClick={() => clickEvent()}>{children}</button>
  )
}
