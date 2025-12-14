import { faAngleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type BreadcrumbProps = {
  segments: string[];
  onSegmentClick: (index: number) => void;
};

export function Breadcrumb({ segments, onSegmentClick }: BreadcrumbProps) {
  return (
    <nav className="flex h-[42px] px-2 sm:px-3 md:px-5 text-gray-700 border border-gray-200 rounded-lg bg-gray-50 min-w-0 max-w-full overflow-hidden" aria-label="Breadcrumb">
      <div className="overflow-x-auto scrollbar-hide w-full flex items-center">
        <ol className="inline-flex items-center space-x-1 md:space-x-2 rtl:space-x-reverse whitespace-nowrap">
          {segments.map((segment, index) => (
            <li key={index} className="inline-flex items-center flex-shrink-0">
              <button
                className="inline-flex items-center text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-950 transition-colors cursor-pointer max-w-16 sm:max-w-24 md:max-w-32 lg:max-w-none truncate"
                onClick={() => onSegmentClick(index)}
                title={segment}
              >
                <span className="truncate">{segment}</span>
              </button>
              {index < segments.length - 1 && (
                <div className="flex items-center ml-2 flex-shrink-0">
                  <FontAwesomeIcon icon={faAngleRight} className="text-gray-400" />
                </div>
              )}
            </li>
          ))}
        </ol>
      </div>
    </nav>
  );
}
