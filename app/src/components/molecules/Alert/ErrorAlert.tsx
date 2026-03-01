import { AlertCircle } from "lucide-react";

type ErrorAlertProps = {
  message: string;
};

/**
 * APIエラーなどのエラーメッセージをインラインで表示する共通コンポーネント
 */
export const ErrorAlert = ({ message }: ErrorAlertProps) => {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 p-4">
      <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
      <p className="text-sm text-red-700 dark:text-red-400">{message}</p>
    </div>
  );
};
