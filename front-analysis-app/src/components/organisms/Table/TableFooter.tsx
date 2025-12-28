import { faChevronLeft, faChevronRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useState } from "react";

export function TableFooter() {
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = 10;
  const itemsPerPage = 10;
  const totalItems = 100; // 仮の値

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
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
            onClick={() => handlePageChange(i)}
            className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 ${currentPage === i ? 'bg-brand-accent text-white hover:bg-brand-accent' : 'text-gray-900'
              }`}
            aria-current={currentPage === i ? 'page' : undefined}
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
          onClick={() => handlePageChange(1)}
          className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 ${currentPage === 1 ? 'bg-brand-accent text-white hover:bg-brand-accent' : 'text-gray-900'
            }`}
          aria-current={currentPage === 1 ? 'page' : undefined}
        >
          1
        </button>
      );

      if (currentPage > 3) {
        pages.push(
          <span key="ellipsis1" className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
            ...
          </span>
        );
      }

      // 現在のページ周辺
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(
          <button
            key={i}
            onClick={() => handlePageChange(i)}
            className={`relative hidden items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 md:inline-flex ${currentPage === i ? 'bg-brand-accent text-white hover:bg-brand-accent' : 'text-gray-900'
              }`}
            aria-current={currentPage === i ? 'page' : undefined}
          >
            {i}
          </button>
        );
      }

      if (currentPage < totalPages - 2) {
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
          onClick={() => handlePageChange(totalPages)}
          className={`relative hidden items-center px-4 py-2 text-sm font-semibold ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 md:inline-flex ${currentPage === totalPages ? 'bg-brand-accent text-white hover:bg-brand-accent' : 'text-gray-900'
            }`}
          aria-current={currentPage === totalPages ? 'page' : undefined}
        >
          {totalPages}
        </button>
      );
    }

    return pages;
  };

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className="flex items-center justify-between mt-4">
      <p className="text-sm text-gray-700">
        Showing <span className="font-medium">{startItem}</span> to <span className="font-medium">{endItem}</span> of{' '}
        <span className="font-medium">{totalItems}</span>
      </p>
      <nav aria-label="Pagination" className="isolate inline-flex -space-x-px rounded-md shadow-sm">
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <span className="sr-only">Previous</span>
          <FontAwesomeIcon icon={faChevronLeft} className="h-5 w-5" />
        </button>
        {renderPageNumbers()}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <span className="sr-only">Next</span>
          <FontAwesomeIcon icon={faChevronRight} className="h-5 w-5" />
        </button>
      </nav>
    </div>
  );
}
