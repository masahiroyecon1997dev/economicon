import { cn } from "@/lib/utils/helpers";
import * as Popover from "@radix-ui/react-popover";
import { Check, ChevronDown } from "lucide-react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";

type SearchableSelectOption = { value: string; label: string };

type SearchableSelectProps = {
  value: string;
  onValueChange: (value: string) => void;
  options: SearchableSelectOption[];
  error?: string;
  className?: string;
  id?: string;
  name?: string;
  placeholder?: string;
  disabled?: boolean;
  "data-testid"?: string;
};

export const SearchableSelect = ({
  value,
  onValueChange,
  options,
  error = "",
  className,
  id,
  name,
  placeholder,
  disabled = false,
  "data-testid": dataTestId,
}: SearchableSelectProps) => {
  const { t } = useTranslation();
  const uid = useId();
  const triggerId = id ?? uid;
  const [open, setOpen] = useState(false);
  const [filterText, setFilterText] = useState("");

  const lowerFilter = filterText.toLowerCase();
  const filtered = options.filter((opt) =>
    opt.label.toLowerCase().includes(lowerFilter),
  );
  const selectedLabel = options.find((opt) => opt.value === value)?.label;

  const handleSelect = (optValue: string) => {
    onValueChange(optValue);
    setOpen(false);
    setFilterText("");
  };

  return (
    <Popover.Root
      open={open}
      onOpenChange={(next) => {
        if (!next) setFilterText("");
        setOpen(next);
      }}
    >
      {name && <input type="hidden" name={name} value={value} />}
      <Popover.Trigger
        id={triggerId}
        data-testid={dataTestId}
        disabled={disabled}
        className={cn(
          "flex w-full items-center justify-between px-2.5 py-1.5 text-sm font-normal",
          "text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 border rounded-md shadow-sm",
          "focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200 cursor-pointer",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error
            ? "border-red-500 focus:ring-red-500 focus:border-red-500"
            : "border-gray-300 dark:border-gray-600 focus:ring-gray-700 dark:focus:ring-gray-400 focus:border-gray-700 dark:focus:border-gray-400 hover:border-gray-400 dark:hover:border-gray-500",
          className,
        )}
      >
        <span
          className={cn(
            "truncate",
            !selectedLabel && "text-gray-400 dark:text-gray-500",
          )}
        >
          {selectedLabel ?? placeholder ?? ""}
        </span>
        <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          sideOffset={4}
          align="start"
          className={cn(
            "relative z-50 overflow-hidden rounded-md border",
            "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-md",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
            "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2",
            "data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
            "min-w-(--radix-popover-trigger-width)",
          )}
        >
          <div className="p-1">
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder={t("Common.FilterColumns")}
              className="mb-1 w-full rounded-md border border-border-color bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 px-2 py-1 text-xs placeholder:text-brand-text-main/40 dark:placeholder:text-gray-500 focus:outline-none focus:ring-1 focus:ring-accent"
            />
            <div className="app-scrollbar max-h-60 overflow-y-auto">
              {filtered.length === 0 ? (
                <p className="p-2 text-xs text-brand-text-main/60">
                  {t("Common.NoColumnsMatchFilter")}
                </p>
              ) : (
                <ul>
                  {filtered.map((opt) => (
                    <li key={opt.value}>
                      <button
                        type="button"
                        onClick={() => handleSelect(opt.value)}
                        className={cn(
                          "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none",
                          "text-gray-900 dark:text-gray-100",
                          "focus:bg-gray-100 dark:focus:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-700",
                        )}
                      >
                        {opt.value === value && (
                          <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                            <Check className="h-4 w-4" />
                          </span>
                        )}
                        {opt.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
