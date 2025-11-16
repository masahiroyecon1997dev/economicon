import type { ChangeEvent, ReactNode } from 'react';

type SelectProps = {
  value: string;
  onChange: (event: ChangeEvent<HTMLSelectElement>) => void;
  children: ReactNode;
  error?: string;
  className?: string;
  id?: string;
};

export const Select = ({
  value,
  onChange,
  children,
  error = '',
  className = '',
  id
}: SelectProps) => {
  const baseClasses = 'w-full px-3 py-2 text-sm font-normal text-gray-900 bg-white border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200 cursor-pointer';
  const errorClasses = error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500 hover:border-gray-400';

  return (
    <select
      id={id}
      value={value}
      onChange={onChange}
      className={`${baseClasses} ${errorClasses} ${className}`}
    >
      {children}
    </select>
  );
};
