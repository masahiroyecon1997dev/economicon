import React from 'react';

type MainTableTdProps = {
  children: string;
}

export function MainTableTd({ children }: MainTableTdProps) {
  return (
    <td className="px-4 py-2 border-b text-sm text-gray-700">{children}</td>
  )
}
