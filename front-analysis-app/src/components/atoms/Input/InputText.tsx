import type { ChangeEvent } from 'react';

type InputTextProps = {
  value: string;
  change: (_event: ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  placeholder?: string;
  type?: 'text' | 'number';
  step?: string;
  id?: string;
  className?: string;
};

export const InputText = ({
  value,
  change,
  error = '',
  placeholder,
  type = 'text',
  step,
  id,
  className = ''
}: InputTextProps) => {
  const baseClasses = 'w-full px-3 py-2 text-sm font-normal text-gray-900 bg-white border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200';
  const errorClasses = error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-gray-700 focus:border-gray-700 hover:border-gray-400';

  return (
    <input
      type={type}
      step={step}
      id={id}
      className={`${baseClasses} ${errorClasses} ${className}`}
      value={value}
      onChange={event => change(event)}
      placeholder={placeholder}
    />
  );
}
