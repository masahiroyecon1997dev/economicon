import { LoadingSpinner } from "../../atoms/Loading/loading-spinner";

type InlineLoadingProps = {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

export const InlineLoading = ({
  message = 'Loading...',
  size = 'md',
  className = ''
}: InlineLoadingProps) => {
  return (
    <div className={`flex items-center justify-center p-4 ${className}`}>
      <LoadingSpinner size={size} />
      {message && (
        <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
          {message}
        </span>
      )}
    </div>
  );
}
