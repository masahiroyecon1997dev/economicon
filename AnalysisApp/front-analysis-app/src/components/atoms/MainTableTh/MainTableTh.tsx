import React from 'react';

type MainTableThProps = {
  children: string;
}

export function MainTableTh({ children }: MainTableThProps) {
  return (
    <th
      className="px-4 py-2 border-b bg-gray-100 text-left text-sm font-semibold text-gray-700">
      {children}
    </th>
  )
}
