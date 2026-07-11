import { cn } from "@/lib/utils/helpers";
import * as Popover from "@radix-ui/react-popover";
import { Plus, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

type TagComboboxOption = { value: string; label: string };

type TagComboboxProps = {
  options: TagComboboxOption[];
  selectedValues: string[];
  onMultipleChange: (values: string[]) => void;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
};

export const TagCombobox = ({
  options,
  selectedValues,
  onMultipleChange,
  error,
  disabled = false,
}: TagComboboxProps) => {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [filterText, setFilterText] = useState("");

  const lowerFilter = filterText.toLowerCase();
  const selectedSet = new Set(selectedValues);

  const notSelected = options.filter(
    (opt) =>
      !selectedSet.has(opt.value) &&
      opt.label.toLowerCase().includes(lowerFilter),
  );
  const alreadySelected = options.filter(
    (opt) =>
      selectedSet.has(opt.value) &&
      opt.label.toLowerCase().includes(lowerFilter),
  );
  const filteredOptions = [...notSelected, ...alreadySelected];

  const removeValue = (val: string) => {
    onMultipleChange(selectedValues.filter((v) => v !== val));
  };

  const addValue = (val: string) => {
    if (!selectedSet.has(val)) {
      onMultipleChange([...selectedValues, val]);
    }
  };

  const selectAll = () => {
    onMultipleChange(options.map((opt) => opt.value));
  };

  const deselectAll = () => {
    onMultipleChange([]);
  };

  return (
    <div className="space-y-2">
      {/* 選択数 + 全選択/全解除 */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-brand-text-sub">
          {t("Common.SelectedCount", {
            count: selectedValues.length,
            total: options.length,
          })}
        </span>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={selectAll}
            disabled={disabled}
            className="text-xs text-brand-accent hover:underline disabled:opacity-50"
          >
            {t("Common.SelectAll")}
          </button>
          <span className="text-xs text-brand-text-sub">/</span>
          <button
            type="button"
            onClick={deselectAll}
            disabled={disabled}
            className="text-xs text-brand-accent hover:underline disabled:opacity-50"
          >
            {t("Common.DeselectAll")}
          </button>
        </div>
      </div>

      {/* Chip 表示エリア */}
      <div
        className={cn(
          "app-scrollbar min-h-9.5 max-h-24 overflow-y-auto rounded-md border p-1.5",
          error
            ? "border-red-500 bg-red-50 dark:bg-red-950/20"
            : "border-border-color bg-secondary",
        )}
      >
        <div className="flex flex-wrap gap-1">
          {selectedValues.map((val) => {
            const label =
              options.find((opt) => opt.value === val)?.label ?? val;
            return (
              <span
                key={val}
                className="inline-flex items-center gap-1 rounded-md border border-brand-accent bg-brand-accent/5 px-2 py-0.5 text-xs text-brand-accent"
              >
                {label}
                <button
                  type="button"
                  onClick={() => removeValue(val)}
                  disabled={disabled}
                  className="disabled:cursor-not-allowed"
                  aria-label={`Remove ${label}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            );
          })}
        </div>
      </div>

      {/* エラー */}
      {error && (
        <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
      )}

      {/* 追加ドロップダウン */}
      <Popover.Root
        open={open}
        onOpenChange={(next) => {
          if (!next) setFilterText("");
          setOpen(next);
        }}
      >
        <Popover.Trigger
          disabled={disabled}
          className="flex items-center gap-1 text-xs text-brand-accent hover:underline disabled:cursor-not-allowed disabled:opacity-50"
          data-testid="tag-combobox-add-trigger"
        >
          <Plus className="h-3.5 w-3.5" />
          {t("Common.AddColumn")}
        </Popover.Trigger>
        <Popover.Portal>
          <Popover.Content
            sideOffset={4}
            align="start"
            className={cn(
              "relative z-50 w-64 overflow-hidden rounded-md border",
              "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-md",
              "data-[state=open]:animate-in data-[state=closed]:animate-out",
              "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
              "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
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
                {filteredOptions.length === 0 ? (
                  <p className="p-2 text-xs text-brand-text-main/60">
                    {t("Common.NoColumnsMatchFilter")}
                  </p>
                ) : (
                  <ul>
                    {filteredOptions.map((opt) => {
                      const isSelected = selectedSet.has(opt.value);
                      return (
                        <li key={opt.value}>
                          <button
                            type="button"
                            onClick={() => !isSelected && addValue(opt.value)}
                            className={cn(
                              "flex w-full items-center rounded-sm px-3 py-1.5 text-sm outline-none",
                              isSelected
                                ? "cursor-default opacity-40 text-brand-text-main"
                                : "cursor-pointer text-gray-900 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700",
                            )}
                          >
                            {opt.label}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
};
