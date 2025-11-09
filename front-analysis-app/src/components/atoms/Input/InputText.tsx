import type { ChangeEvent } from 'react';

type InputTextProps = {
  value: string;
  change: (_event: ChangeEvent<HTMLInputElement>) => void;
  error: string;
};

export const InputText = ({ value, change, error }: InputTextProps) => {
  return (
    <input
      type="text"
      className={`border ${error !== '' ? 'border-red-300' : 'border-gray-300'
        } h-9 block w-full max-w-xs px-4 py-1 text-sm font-normal shadow-xs text-gray-900 bg-transparent rounded-md placeholder-gray-400 focus:outline-none leading-relaxed`}
      value={value}
      onChange={event => change(event)}
    />
  );
}
