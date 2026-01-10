import * as RadixDialog from '@radix-ui/react-dialog';

import { useMessageDialogStore } from '../../../stores/useMessageDialogStore';
import { ErrorModalFooter } from './error-modal-footer';
import { ModalHeader } from './modal-header';

export function MessageDialog() {
  const { isOpen, title, message, closeMessageDialog } = useMessageDialogStore();

  const handleOk = () => {
    closeMessageDialog();
  };

  const handleClose = () => {
    closeMessageDialog();
  };

  return (
    <RadixDialog.Root open={isOpen} onOpenChange={(open) => !open && closeMessageDialog()}>
      <RadixDialog.Portal>
        <RadixDialog.Overlay className="fixed inset-0 z-50 bg-gray-900/50 data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out" />
        <RadixDialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 p-4 data-[state=open]:animate-fade-in-down data-[state=closed]:animate-fade-out-up"
          onEscapeKeyDown={handleClose}
        >
          <div className="relative bg-white rounded-lg shadow">
            <ModalHeader close={handleClose}>{title}</ModalHeader>
            <RadixDialog.Description asChild>
              <div className="p-4 md:p-5">
                <p className="text-sm text-gray-900 whitespace-pre-wrap">
                  {message}
                </p>
              </div>
            </RadixDialog.Description>
            <ErrorModalFooter onOk={handleOk} />
          </div>
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
