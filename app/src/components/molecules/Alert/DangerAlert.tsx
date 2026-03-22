import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

type DangerAlertProps = {
  children: ReactNode;
};

/**
 * 危険操作の警告バナー
 * 削除確認など不可逆な操作の前に表示する共通コンポーネント
 */
export const DangerAlert = ({ children }: DangerAlertProps) => {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 p-4">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
      <p className="text-sm text-red-700 dark:text-red-400">{children}</p>
    </div>
  );
};
