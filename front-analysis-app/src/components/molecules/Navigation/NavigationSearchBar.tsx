import { UpDirectoryButton } from "../../atoms/Button/UpDirectoryButton";
import { FileSearchInput } from "../../atoms/Input/FileSearchInput";
import { Breadcrumb } from "./Breadcrumb";

type NavigationSearchBarProps = {
  pathSegments: string[];
  searchValue: string;
  searchPlaceholder: string;
  upDirectoryTitle: string;
  onUpDirectory: () => void;
  onBreadcrumbClick: (index: number) => void;
  onSearchChange: (value: string) => void;
};

export function NavigationSearchBar({
  pathSegments,
  searchValue,
  searchPlaceholder,
  upDirectoryTitle,
  onUpDirectory,
  onBreadcrumbClick,
  onSearchChange
}: NavigationSearchBarProps) {
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <UpDirectoryButton
          onClick={onUpDirectory}
          title={upDirectoryTitle}
        />
        <Breadcrumb
          segments={pathSegments}
          onSegmentClick={onBreadcrumbClick}
        />
      </div>
      <div className="flex-1">
        <FileSearchInput
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={onSearchChange}
        />
      </div>
    </div>
  );
}
