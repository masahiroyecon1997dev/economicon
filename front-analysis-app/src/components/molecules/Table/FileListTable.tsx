import { faFileLines, faFolder } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { FileType } from "../../../types/commonTypes";

type FileListTableProps = {
  files: FileType[];
  onFileDoubleClick: (file: FileType) => void;
  fileNameHeader: string;
  sizeHeader: string;
  lastModifiedHeader: string;
  maxHeight?: string;
};

export function FileListTable({
  files,
  onFileDoubleClick,
  fileNameHeader,
  sizeHeader,
  lastModifiedHeader,
  maxHeight = "400px"
}: FileListTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-primary/20">
      <div className="overflow-y-auto" style={{ maxHeight }}>
        <table className="w-full">
          <thead className="bg-primary/5 dark:bg-primary/10 sticky top-0">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60 w-12">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                {fileNameHeader}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                {sizeHeader}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-black/60 dark:text-white/60">
                {lastModifiedHeader}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-primary/20 bg-background-light dark:bg-background-dark">
            {files.map((file, index) => (
              <tr
                key={index}
                className="hover:bg-primary/5 dark:hover:bg-primary/10 transition-colors"
                onDoubleClick={() => onFileDoubleClick(file)}
                style={{ cursor: file.isFile ? 'default' : 'pointer' }}
              >
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <FontAwesomeIcon
                    icon={file.isFile ? faFileLines : faFolder}
                    className={file.isFile ? 'text-blue-500' : 'text-yellow-500'}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-black dark:text-white">
                  <div className="flex items-center gap-2">
                    <span className={file.isFile ? '' : 'font-semibold'}>
                      {file.name}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">
                  {file.isFile && <span>{file.size}</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-black/60 dark:text-white/60">
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
