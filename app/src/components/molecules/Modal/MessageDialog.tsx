import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { useMessageDialogStore } from "../../../stores/messageDialog";
import { ErrorModalFooter } from "./ErrorModalFooter";

export const MessageDialog = () => {
  const { isOpen, title, message, closeMessageDialog } =
    useMessageDialogStore();

  const handleOk = () => {
    closeMessageDialog();
  };

  const handleClose = () => {
    closeMessageDialog();
  };

  return (
    <RadixDialog.Root
      open={isOpen}
      onOpenChange={(open) => !open && closeMessageDialog()}
    >
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-gray-900/50 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out" />
        <RadixDialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white dark:bg-gray-900 shadow-lg data-[state=open]:animate-fade-in-down data-[state=closed]:animate-fade-out-up overflow-hidden"
          onEscapeKeyDown={handleClose}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-b-gray-300 dark:border-b-gray-700 rounded-t">
            <RadixDialog.Title className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </RadixDialog.Title>
            <RadixDialog.Close asChild>
              <button
                type="button"
                className="text-gray-400 bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-gray-100 rounded-lg text-sm w-8 h-8 inline-flex justify-center items-center"
                aria-label="閉じる"
              >
                <X className="w-5 h-5" />
              </button>
            </RadixDialog.Close>
          </div>

          {/* Content */}
          <RadixDialog.Description asChild>
            <div className="p-4 md:p-5">
              <p className="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap">
                {message}
              </p>
            </div>
          </RadixDialog.Description>

          {/* Footer */}
          <ErrorModalFooter onOk={handleOk} />
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
};
