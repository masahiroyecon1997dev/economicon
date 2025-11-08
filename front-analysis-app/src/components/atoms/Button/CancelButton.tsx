type CancelButtonProps = {
  children: string;
  cancel: () => void;
};

export const CancelButton = ({ children, cancel }: CancelButtonProps) => {
  return (
    <button
      className="w-28 h-9 px-5 py-2.5 ms-3
            text-center text-xs text-gray-900 font-medium
            rounded-full focus:ring-4 focus:outline-none border
            bg-white border-gray-200
            hover:bg-gray-100 hover:text-blue-700
            focus:ring-gray-100
            dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700"
      onClick={() => cancel()}
    >
      {children}
    </button>
  );
}
