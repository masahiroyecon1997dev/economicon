/**
 * テーブル操作ダイアログ
 *
 * TableNavItem からの操作イベントを受け取り、
 * 対応するフォームコンポーネントを Radix Dialog で表示する。
 */
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { DeleteTableForm } from "./TableOperationForms/DeleteTableForm";
import { DuplicateTableForm } from "./TableOperationForms/DuplicateTableForm";
import { RenameTableForm } from "./TableOperationForms/RenameTableForm";

export type TableOperation = "rename" | "duplicate" | "delete";

type TableOperationDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  operation: TableOperation | null;
  tableName: string;
};

const getDialogTitle = (
  operation: TableOperation | null,
  t: (key: string) => string,
): string => {
  switch (operation) {
    case "rename":
      return t("RenameTableForm.Title");
    case "duplicate":
      return t("DuplicateTableForm.Title");
    case "delete":
      return t("DeleteTableForm.Title");
    default:
      return "";
  }
};

export const TableOperationDialog = ({
  open,
  onOpenChange,
  operation,
  tableName,
}: TableOperationDialogProps) => {
  const { t } = useTranslation();

  if (!operation) return null;

  const handleSuccess = () => {
    onOpenChange(false);
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  const renderForm = () => {
    switch (operation) {
      case "rename":
        return (
          <RenameTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            onClose={handleClose}
          />
        );
      case "duplicate":
        return (
          <DuplicateTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            onClose={handleClose}
          />
        );
      case "delete":
        return (
          <DeleteTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            onClose={handleClose}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-gray-900/40 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out" />
        <Dialog.Content className="fixed left-1/2 top-[48%] z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white dark:bg-gray-900 shadow-xl overflow-hidden">
          {/* ヘッダー */}
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-4">
            <div>
              <Dialog.Title className="text-base font-semibold text-gray-900 dark:text-gray-100">
                {getDialogTitle(operation, t)}
              </Dialog.Title>
              <p className="mt-0.5 text-xs font-mono text-gray-500 dark:text-gray-400 truncate max-w-64">
                {tableName}
              </p>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="rounded-lg p-1.5 text-gray-400 dark:text-gray-500 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
                aria-label={t("Common.Close")}
              >
                <X className="h-4 w-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* フォーム本体 */}
          <Dialog.Description asChild>
            <div className="px-5 py-4 dark:text-gray-200">{renderForm()}</div>
          </Dialog.Description>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
