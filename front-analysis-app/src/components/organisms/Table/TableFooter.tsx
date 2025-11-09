export function TableFooter() {
  return (
    <div className="flex items-center justify-between mt-4">
      <p className="text-sm text-gray-700">
        Showing <span className="font-medium">1</span> to <span className="font-medium">10</span> of{' '}
      </p>
      <nav aria-label="Pagination" className="isolate inline-flex -space-x-px rounded-md shadow-sm">
        <a className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0" href="#">
        <span className="sr-only">Previous</span>
        <svg aria-hidden="true" className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path clip-rule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" fill-rule="evenodd"></path>
        </svg>
        </a>
        <a className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0" href="#">1</a>
        <a className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0" href="#">2</a>
        <a className="relative hidden items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 md:inline-flex" href="#">3</a>
        <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300 focus:outline-offset-0">...</span>
        <a className="relative hidden items-center px-4 py-2 text-sm font-semibold text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 md:inline-flex" href="#">10</a>
        <a className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0" href="#">
        <span className="sr-only">Next</span>
        <svg aria-hidden="true" className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
        <path clip-rule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" fill-rule="evenodd"></path>
        </svg>
        </a>
      </nav>
    </div>
  );
}
