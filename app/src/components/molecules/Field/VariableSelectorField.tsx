import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/helpers";
import type { ColumnType } from "@/types/commonTypes";

type VariableSelectorMode = "single" | "multiple";

type VariableSelectorFieldProps = {
  label: string;
  description?: string;
  mode: VariableSelectorMode;
  columns: ColumnType[];
  selectedValue?: string;
  selectedValues?: string[];
  onSingleChange?: (value: string) => void;
  onMultipleChange?: (values: string[]) => void;
  error?: string;
  disabled?: boolean;
  className?: string;
  name?: string;
};

export const VariableSelectorField = ({
  label,
  description,
  mode,
  columns,
  selectedValue = "",
  selectedValues = [],
  onSingleChange,
  onMultipleChange,
  error,
  disabled = false,
  className,
  name,
}: VariableSelectorFieldProps) => {
  const { t } = useTranslation();

  const handleRadioChange = (columnName: string) => {
    if (mode === "single" && onSingleChange) {
      onSingleChange(columnName);
    }
  };

  const handleCheckboxChange = (columnName: string) => {
    if (mode === "multiple" && onMultipleChange) {
      if (selectedValues.includes(columnName)) {
        onMultipleChange(selectedValues.filter((v) => v !== columnName));
      } else {
        onMultipleChange([...selectedValues, columnName]);
      }
    }
  };

  const [filterText, setFilterText] = useState("");
  const lowerFilter = filterText.toLowerCase();
  const matchesFilter = (col: ColumnType) =>
    col.name.toLowerCase().includes(lowerFilter);
  const visibleColumns =
    mode === "multiple"
      ? [
          // 選択済だがフィルタで非表示になる項目を先頭にピン留め
          ...columns.filter(
            (col) => selectedValues.includes(col.name) && !matchesFilter(col),
          ),
          // フィルタ一致する項目
          ...columns.filter(matchesFilter),
        ]
      : columns.filter(matchesFilter);

  return (
    <div className={cn("flex flex-col", className)}>
      <label
        htmlFor={`variable-selector-field-search-${name || "default"}`}
        className="mb-1.5 block text-xs font-medium text-brand-text-main"
      >
        {label}
      </label>
      {description && (
        <p className="mb-2 text-xs text-brand-text-main/60">{description}</p>
      )}
      {columns.length > 0 && (
        <input
          type="text"
          id={`variable-selector-field-search-${name || "default"}`}
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          placeholder={t("Common.FilterColumns")}
          disabled={disabled}
          className="mb-1.5 w-full rounded-md border border-border-color bg-white px-2 py-1 text-xs placeholder:text-brand-text-main/40 focus:outline-none focus:ring-1 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-50"
        />
      )}
      <div
        className={cn(
          "app-scrollbar min-h-0 flex-1 overflow-y-auto rounded-lg border px-2 py-1",
          error
            ? "border-red-500 bg-red-50"
            : "border-border-color bg-secondary",
        )}
      >
        {columns.length === 0 ? (
          <p className="p-1 text-xs text-brand-text-main/60">
            {t("Common.NoColumnsAvailable")}
          </p>
        ) : visibleColumns.length === 0 ? (
          <p className="p-1 text-xs text-brand-text-main/60">
            {t("Common.NoColumnsMatchFilter")}
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {visibleColumns.map((column, index) => (
              <li key={index}>
                <label
                  htmlFor={`variable-selector-field-${column.name}-${name || "default"}`}
                  className={cn(
                    "flex w-full cursor-pointer items-center gap-3 rounded-md p-0.5",
                    disabled
                      ? "cursor-not-allowed opacity-50"
                      : "hover:bg-white",
                  )}
                >
                  {mode === "single" ? (
                    <input
                      id={`variable-selector-field-${column.name}-${name || "default"}`}
                      className="h-4 w-4 border-gray-300 text-accent focus:ring-accent"
                      type="radio"
                      name={name || "variable-selector-single"}
                      value={column.name}
                      checked={selectedValue === column.name}
                      onChange={() => handleRadioChange(column.name)}
                      disabled={disabled}
                    />
                  ) : (
                    <input
                      id={`variable-selector-field-${column.name}-${name || "default"}`}
                      className="h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
                      type="checkbox"
                      name={name || "variable-selector-multiple"}
                      value={column.name}
                      checked={selectedValues.includes(column.name)}
                      onChange={() => handleCheckboxChange(column.name)}
                      disabled={disabled}
                    />
                  )}
                  <span className="text-sm">{column.name}</span>
                </label>
              </li>
            ))}
          </ul>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
};
