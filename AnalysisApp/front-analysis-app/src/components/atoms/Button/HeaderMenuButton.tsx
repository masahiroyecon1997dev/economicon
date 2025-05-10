import React from 'react';

type HeaderMenuButtonProps = {
  children: string;
  clickEvent: () => void;
};

export function HeaderMenuButton({ children, clickEvent }: HeaderMenuButtonProps) {
  return (
    <button
      className="w-24 px-4 py-2 hover:bg-gray-200 whitespace-nowrap text-left"
      onClick={() => clickEvent()}
    >
      {children}
    </button>
  );
}
