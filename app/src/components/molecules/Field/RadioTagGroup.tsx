import { cn } from "../../../lib/utils/helpers";

type RadioTagItem = {
  value: string;
  label: string;
};

type RadioTagGroupProps = {
  name: string;
  items: RadioTagItem[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  error?: string;
};

export const RadioTagGroup = ({
  name,
  items,
  value,
  onChange,
  disabled = false,
  error,
}: RadioTagGroupProps) => {
  return (
    <div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const isSelected = item.value === value;
          return (
            <label
              key={item.value}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                isSelected
                  ? "border-brand-accent bg-brand-accent/5 text-brand-accent"
                  : "border-border-color bg-secondary text-brand-text-main hover:border-brand-accent/50",
                disabled && "cursor-not-allowed opacity-50",
              )}
            >
              <input
                type="radio"
                name={name}
                value={item.value}
                checked={isSelected}
                onChange={() => onChange(item.value)}
                disabled={disabled}
                className="h-3.5 w-3.5 border-gray-300 text-brand-accent focus:ring-brand-accent"
              />
              <span>{item.label}</span>
            </label>
          );
        })}
      </div>
      {error && <p className="mt-1.5 text-xs text-red-600">{error}</p>}
    </div>
  );
};
