import type { ReactNode } from "react";

type FormFieldProps = {
  label: string;
  children: ReactNode;
  error?: string;
  htmlFor?: string;
  className?: string;
};

export const FormField = ({
  label,
  children,
  error,
  htmlFor,
  className = "",
}: FormFieldProps) => {
  return (
    <div className={`space-y-1 ${className}`}>
      <label
        className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        htmlFor={htmlFor}
      >
        {label}
      </label>
      {children}
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">{error}</p>
      )}
    </div>
  );
};
