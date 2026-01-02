import { faFileLines, faFolder, faSort, faSortDown, faSortUp } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useTranslation } from "react-i18next";
import type { FileType, SortDirection, SortField } from "../../../types/commonTypes";

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
  const { t } = useTranslation();

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
    <div className="overflow-hidden rounded-xl border border-brand-primary/20 w-full">
      <div className="overflow-y-auto overflow-x-auto" style={{ maxHeight }}>
        <table className="w-full min-w-96" title={t('SelectFileView.FileListTableTitle')}>
          <thead className="bg-brand-primary-light sticky top-0">
            <tr>
              <th
                className={`px-2 sm:px-3 md:px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider min-w-0 ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('name')}
                style={{ width: '50%', minWidth: '120px' }}
              >
                <div className="flex items-center">
                  <span className="truncate">{fileNameHeader}</span>
                  {onSort && getSortIcon('name')}
                </div>
              </th>
              <th
                className={`px-2 sm:px-3 md:px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider min-w-0 hidden sm:table-cell ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('size')}
                style={{ width: '25%', minWidth: '80px' }}
              >
                <div className="flex items-center">
                  <span className="truncate">{sizeHeader}</span>
                  {onSort && getSortIcon('size')}
                </div>
              </th>
              <th
                className={`px-2 sm:px-3 md:px-6 py-3 text-left text-xs text-white font-medium uppercase tracking-wider min-w-0 ${onSort ? 'cursor-pointer hover:bg-brand-primary-light/80 transition-colors' : ''
                  }`}
                onClick={() => handleHeaderClick('modifiedTime')}
                style={{ width: '25%', minWidth: '100px' }}
              >
                <div className="flex items-center">
                  <span className="truncate">{lastModifiedHeader}</span>
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
                <td className="px-2 sm:px-3 md:px-6 py-4 text-sm font-medium text-black min-w-0" style={{ width: '50%', minWidth: '120px' }}>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="shrink-0">
                      <FontAwesomeIcon
                        icon={file.isFile ? faFileLines : faFolder}
                        className={file.isFile ? 'text-blue-500' : 'text-yellow-500'}
                      />
                    </span>
                    <span
                      className={`truncate block min-w-0 ${file.isFile ? '' : 'font-semibold'}`}
                      style={{ maxWidth: 'min(400px, calc(50vw - 100px))' }}
                    >
                      {file.name}
                    </span>
                  </div>
                </td>
                <td className="px-2 sm:px-3 md:px-6 py-4 text-sm text-black/60 min-w-0 hidden sm:table-cell" style={{ width: '25%', minWidth: '80px' }}>
                  {file.isFile && <span className="truncate block">{file.size}</span>}
                </td>
                <td className="px-2 sm:px-3 md:px-6 py-4 text-sm text-black/60 min-w-0" style={{ width: '25%', minWidth: '100px' }}>
                  {file.isFile && <span className="truncate block">{file.modifiedTime}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
