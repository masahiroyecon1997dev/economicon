import { faAngleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type BreadcrumbProps = {
  segments: string[];
  onSegmentClick: (index: number) => void;
};

export function Breadcrumb({ segments, onSegmentClick }: BreadcrumbProps) {
  return (
    <nav className="flex px-5 py-3 text-gray-700 border border-gray-200 rounded-lg bg-gray-50 dark:bg-gray-800 dark:border-gray-700" aria-label="Breadcrumb">
      <ol className="inline-flex items-center space-x-1 md:space-x-2 rtl:space-x-reverse">
        {segments.map((segment, index) => (
          <li key={index} className="inline-flex items-center">
            <button
              className="inline-flex items-center text-sm font-medium text-gray-700 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white transition-colors"
              onClick={() => onSegmentClick(index)}
            >
              {segment}
            </button>
            {index < segments.length - 1 && (
              <div className="flex items-center ml-2">
                <FontAwesomeIcon icon={faAngleRight} className="text-gray-400" />
              </div>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
