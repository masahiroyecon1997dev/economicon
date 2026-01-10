import { LoadingSpinner } from "../../atoms/Loading/loading-spinner";

type LoadingOverlayProps = {
  isVisible: boolean;
  message?: string;
  backdrop?: boolean;
};

export const LoadingOverlay = ({
  isVisible,
  message = 'Loading...',
  backdrop = true
}: LoadingOverlayProps) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center ${backdrop ? 'bg-black/50' : ''
      }`}>
      <div className="flex flex-col items-center justify-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
        <LoadingSpinner size="lg" />
        {message && (
          <p className="mt-4 text-sm font-medium text-gray-700 dark:text-gray-300">
            {message}
          </p>
        )}
      </div>
    </div>
  );
}
