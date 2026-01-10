import { cn } from "../../../common/utils";

type CancelButtonProps = {
  children: string;
  cancel: () => void;
  className?: string;
};

export const CancelButton = ({ children, cancel, className }: CancelButtonProps) => {
  return (
    <button
      onClick={cancel}
      className={cn(
        "rounded-md px-6 py-2.5 text-sm font-semibold text-main dark:text-gray-300",
        "bg-white dark:bg-gray-700 border border-border-color dark:border-gray-600",
        "hover:bg-gray-50 dark:hover:bg-gray-600 cursor-pointer transition-colors",
        className
      )}
      aria-label="cancel"
    >
      {children}
    </button>
  );
}
