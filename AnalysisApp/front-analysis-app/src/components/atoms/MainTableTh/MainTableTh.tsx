import React from "react";

type MainTableThProps = {
  children: string;
};

export function MainTableTh({ children }: MainTableThProps) {
  return (
    <th className="border-t px-4 py-2 bg-gray-100 text-left text-sm font-semibold text-gray-700 sticky top-0 z-10">
      {children}
    </th>
  );
}
