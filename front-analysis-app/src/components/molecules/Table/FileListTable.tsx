import { faFileLines, faFolder, faSort, faSortDown, faSortUp } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { FileType } from "../../../types/commonTypes";
import type { SortDirection, SortField } from "../../../types/stateTypes";

type FileListTableProps = {
  files: FileType[];
  onFileClick: (file: FileType) => void;
  fileNameHeader: string;
  sizeHeader: string;
  lastModifiedHeader: string;
  maxHeight?: string;
  sortField?: SortField | null;
  sortDirection?: SortDirection;
  onSort?: (field: SortField) => void;
};

export function FileListTable({
  files,
  onFileClick,
  fileNameHeader,
  sizeHeader,
  lastModifiedHeader,
  maxHeight = "400px",
  sortField = null,
  sortDirection = null,
  onSort
}: FileListTableProps) {

  // ソートアイコンを返す関数
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <FontAwesomeIcon icon={faSort} className="ml-1 text-gray-400" />;
    }
    if (sortDirection === 'asc') {
      return <FontAwesomeIcon icon={faSortUp} className="ml-1 text-blue-500" />;
    }
    if (sortDirection === 'desc') {
      return <FontAwesomeIcon icon={faSortDown} className="ml-1 text-blue-500" />;
    }
    return <FontAwesomeIcon icon={faSort} className="ml-1 text-gray-400" />;
  };

  // ヘッダークリックハンドラー
  const handleHeaderClick = (field: SortField) => {
    if (onSort) {
      onSort(field);
    }
  };

  return (
    <div className="overflow-hidden rounded-xl border border-brand-primary/20">
      <div className="overflow-y-auto" style={{ maxHeight }}>
        <table className="w-full">
          <thead className="bg-brand-primary-light sticky top-0">
            <tr>
              <th
                className={`px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider text-black/60 ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('name')}
              >
                <div className="flex items-center">
                  {fileNameHeader}
                  {onSort && getSortIcon('name')}
                </div>
              </th>
              <th
                className={`px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider text-black/60 ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('size')}
              >
                <div className="flex items-center">
                  {sizeHeader}
                  {onSort && getSortIcon('size')}
                </div>
              </th>
              <th
                className={`px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider text-black/60 ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('modifiedTime')}
              >
                <div className="flex items-center">
                  {lastModifiedHeader}
                  {onSort && getSortIcon('modifiedTime')}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-primary/20 bg-background-light">
            {files.map((file, index) => (
              <tr
                key={index}
                className="hover:bg-brand-primary/5 transition-colors cursor-pointer"
                onClick={() => onFileClick(file)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black">
                  <div className="flex items-center gap-2">
                    <span>
                      <FontAwesomeIcon
                        icon={file.isFile ? faFileLines : faFolder}
                        className={file.isFile ? 'text-blue-500' : 'text-yellow-500'}
                      />
                    </span>
                    <span className={file.isFile ? '' : 'font-semibold'}>
                      {file.name}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60">
                  {file.isFile && <span>{file.size}</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60">
                  {file.isFile && <span>{file.modifiedTime}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
