import { type ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from "../../../functions/utils";

type InputTextProps = {
  value: string;
  change: (_event: ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  placeholder?: string;
  type?: 'text' | 'number';
  step?: string;
  id?: string;
  className?: string;
  disabled?: boolean;
};

export const InputText = ({
  value,
  change,
  error = '',
  placeholder,
  type = 'text',
  step,
  id,
  className,
  disabled = false,
}: InputTextProps) => {
  const { t } = useTranslation();

  return (
    <div className="w-full">
      <input
        type={type}
        step={step}
        id={id}
        className={cn(
          "w-full px-2.5 py-1.5 text-sm font-normal text-gray-900 bg-white border rounded-md shadow-sm",
          "placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200",
          error
            ? "border-red-500 focus:ring-red-500 focus:border-red-500"
            : "border-gray-300 focus:ring-gray-700 focus:border-gray-700 hover:border-gray-400",
          className
        )}
        value={value}
        onChange={event => change(event)}
        placeholder={placeholder}
        disabled={disabled}
      />
      <div className="h-4 mt-0.5">
        {error && (
          <p className="text-xs text-red-600">
            {t(error)}
          </p>
        )}
      </div>
    </div>
  );
}
