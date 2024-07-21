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
