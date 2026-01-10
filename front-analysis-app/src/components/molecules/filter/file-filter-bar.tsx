import { FileFilterButton } from "../../atoms/Button/file-filter-button";

type FilterOption = {
  label: string;
  value: string;
  isActive: boolean;
};

type FileFilterBarProps = {
  filters: FilterOption[];
  onFilterClick: (filterValue: string) => void;
};

export function FileFilterBar({ filters, onFilterClick }: FileFilterBarProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {filters.map((filter) => (
        <FileFilterButton
          key={filter.value}
          isActive={filter.isActive}
          onClick={() => onFilterClick(filter.value)}
        >
          {filter.label}
        </FileFilterButton>
      ))}
    </div>
  );
}
