import { ChevronLeft, ChevronRight } from "lucide-react";
import type { TableInfoType } from '../../../types/commonTypes';

type TableFooterProps = {
  tableInfo: TableInfoType;
  onPageChange: (tableName: string, page: number) => void;
};

export const TableFooter = ({ tableInfo, onPageChange }: TableFooterProps) => {
  if (!tableInfo) {
    return null;
  }

  const { startRow, endRow, totalRows, pageIndex, totalPages } = tableInfo;

  const handlePageChange = (tableName: string, page: number) => {
    if (page >= 1 && page <= totalPages) {
      onPageChange(tableName, page);
    }
  };

  const renderPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 3;

    if (totalPages <= maxVisiblePages + 2) {
      // 全ページを表示
      for (let i = 1; i <= totalPages; i++) {
        pages.push(
          <button
            key={i}
            onClick={() => handlePageChange(tableInfo.tableName, i)}
            className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 focus:z-20 focus:outline-offset-0 cursor-pointer transition-colors ${pageIndex === i ? 'bg-brand-accent text-white hover:bg-brand-accent-dark' : 'text-gray-900 hover:bg-gray-200 hover:text-gray-950'
              }`}
            aria-current={pageIndex === i ? 'page' : undefined}
          >
            {i}
          </button>
        );
      }
    } else {
      // 1ページ目
      pages.push(
        <button
          key={1}
          onClick={() => handlePageChange(tableInfo.tableName, 1)}
          className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 focus:z-20 focus:outline-offset-0 cursor-pointer transition-colors ${pageIndex === 1 ? 'bg-brand-accent text-white hover:bg-brand-accent-dark' : 'text-gray-900 hover:bg-gray-200 hover:text-gray-950'
            }`}
          aria-current={pageIndex === 1 ? 'page' : undefined}
        >
          1
        </button>
      );

      if (pageIndex > 3) {
        pages.push(
          <span key="ellipsis1" className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
            ...
          </span>
        );
      }

      // 現在のページ周辺
      const start = Math.max(2, pageIndex - 1);
      const end = Math.min(totalPages - 1, pageIndex + 1);

      for (let i = start; i <= end; i++) {
        pages.push(
          <button
            key={i}
            onClick={() => handlePageChange(tableInfo.tableName, i)}
            className={`relative hidden items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 focus:z-20 focus:outline-offset-0 md:inline-flex cursor-pointer transition-colors ${pageIndex === i ? 'bg-brand-accent text-white hover:bg-brand-accent-dark' : 'text-gray-900 hover:bg-gray-200 hover:text-gray-950'
              }`}
            aria-current={pageIndex === i ? 'page' : undefined}
          >
            {i}
          </button>
        );
      }

      if (pageIndex < totalPages - 2) {
        pages.push(
          <span key="ellipsis2" className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
            ...
          </span>
        );
      }

      // 最終ページ
      pages.push(
        <button
          key={totalPages}
          onClick={() => handlePageChange(tableInfo.tableName, totalPages)}
          className={`relative hidden items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 focus:z-20 focus:outline-offset-0 md:inline-flex cursor-pointer transition-colors ${pageIndex === totalPages ? 'bg-brand-accent text-white hover:bg-brand-accent-dark' : 'text-gray-900 hover:bg-gray-200 hover:text-gray-950'
            }`}
          aria-current={pageIndex === totalPages ? 'page' : undefined}
        >
          {totalPages}
        </button>
      );
    }

    return pages;
  };
  return (
    <div className="flex items-center justify-between mt-4">
      <p className="text-sm text-gray-700">
        Showing <span className="font-medium">{startRow}</span> to <span className="font-medium">{endRow}</span> of{' '}
        <span className="font-medium">{totalRows}</span>
      </p>
      <nav aria-label="Pagination" className="isolate inline-flex -space-x-px rounded-md shadow-sm">
        <button
          onClick={() => handlePageChange(tableInfo.tableName, pageIndex - 1)}
          disabled={pageIndex === 1}
          className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-200 hover:text-gray-600 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
          aria-label="Previous page"
        >
          <span className="sr-only">Previous</span>
          <ChevronLeft className="h-5 w-5" />
        </button>
        {renderPageNumbers()}
        <button
          onClick={() => handlePageChange(tableInfo.tableName, pageIndex + 1)}
          disabled={pageIndex === totalPages}
          className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-200 hover:text-gray-600 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors"
          aria-label="Next page"
        >
          <span className="sr-only">Next</span>
          <ChevronRight className="h-5 w-5" />
        </button>
      </nav>
    </div>
  );
}
