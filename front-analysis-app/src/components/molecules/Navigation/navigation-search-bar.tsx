import { UpDirectoryButton } from "../../atoms/Button/up-directory-button";
import { SearchInput } from "../../atoms/Input/search-input";
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
    <div className="w-full">
      {/* 幅が十分にある場合（768px以上）は横並び */}
      <div className="hidden md:flex items-center gap-3 w-full">
        <div className="flex items-center gap-1.5 min-w-0 flex-1 overflow-hidden">
          <div className="shrink-0">
            <UpDirectoryButton
              onClick={onUpDirectory}
              title={upDirectoryTitle}
            />
          </div>
          <div className="min-w-0 max-w-2xl overflow-hidden">
            <Breadcrumb
              segments={pathSegments}
              onSegmentClick={onBreadcrumbClick}
            />
          </div>
        </div>
        <div className="shrink-0 w-64 lg:w-80">
          <SearchInput
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={onSearchChange}
          />
        </div>
      </div>

      {/* 幅が狭い場合（768px未満）は縦積み */}
      <div className="flex flex-col gap-2 md:hidden">
        <div className="flex items-center gap-1.5 min-w-0 w-full">
          <div className="shrink-0">
            <UpDirectoryButton
              onClick={onUpDirectory}
              title={upDirectoryTitle}
            />
          </div>
          <div className="min-w-0 flex-1 overflow-hidden">
            <Breadcrumb
              segments={pathSegments}
              onSegmentClick={onBreadcrumbClick}
            />
          </div>
        </div>
        <div className="w-full">
          <SearchInput
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={onSearchChange}
          />
        </div>
      </div>
    </div>
  );
}
