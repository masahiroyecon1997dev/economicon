import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../../atoms/Button/Button";

type DialogProps = {
  isOpenDialog: boolean;
  children: ReactNode;
  modalTitle: string;
  submitButtonName: string;
  submit: () => void;
  close: () => void;
  modalSize: string;
};

export const Dialog = ({
  isOpenDialog,
  children,
  modalTitle,
  submitButtonName,
  submit,
  close,
  modalSize,
}: DialogProps) => {
  const { t } = useTranslation();

  return (
    <Dialog.Root open={isOpenDialog} onOpenChange={(open) => !open && close()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-gray-900/50 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out" />
        <Dialog.Content
          className={`fixed left-1/2 top-1/2 z-50 w-full ${modalSize} max-h-[85vh] -translate-x-1/2 -translate-y-1/2 rounded-lg bg-white shadow-lg data-[state=open]:animate-fade-in-down data-[state=closed]:animate-fade-out-up overflow-hidden`}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 md:p-5 border-b border-b-gray-300 rounded-t">
            <Dialog.Title className="text-xl font-semibold text-gray-900">
              {modalTitle}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                type="button"
                className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 inline-flex justify-center items-center"
                aria-label="閉じる"
              >
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Content */}
          <Dialog.Description asChild>
            <div className="p-4 md:p-5 overflow-y-auto">{children}</div>
          </Dialog.Description>

          {/* Footer */}
          <div className="flex items-center justify-end gap-2 p-4 md:p-5 border-t border-gray-200 rounded-b">
            <Button onClick={close} variant="outline">
              {t("Common.Cancel")}
            </Button>
            {submitButtonName !== "" && (
              <Button onClick={submit} variant="primary">
                {submitButtonName}
              </Button>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
