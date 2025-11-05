import { useEffect, useState } from 'react';

import { useErrorDialogStore } from '../../../stores/useErrorDialogStore';
import { ErrorModalFooter } from './ErrorModalFooter';
import { ModalHeader } from './ModalHeader';

export function ErrorDialog() {
  const { isOpen, title, message, closeErrorDialog } = useErrorDialogStore();
  const [isModalBlock, setIsModalBlock] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setIsModalBlock(isOpen);
    } else {
      setTimeout(() => {
        setIsModalBlock(isOpen);
      }, 400);
    }
  }, [isOpen]);

  const handleOk = () => {
    closeErrorDialog();
  };

  const handleClose = () => {
    closeErrorDialog();
  };

  return (
    <div
      className={`fixed inset-0 z-50 justify-center items-center overflow-y-auto overflow-x-hidden w-full md:inset-0 bg-gray-900/50 ${
        isModalBlock ? 'flex' : 'hidden'
      }`}
    >
      <div
        className={`relative p-4 w-full max-w-md max-h-full transform ${
          isOpen ? 'animate-fade-in-down' : 'animate-fade-out-up'
        }`}
      >
        <div className="relative bg-white rounded-lg shadow dark:bg-gray-700">
          <ModalHeader close={handleClose}>{title}</ModalHeader>
          <div className="p-4 md:p-5">
            <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
              {message}
            </p>
          </div>
          <ErrorModalFooter onOk={handleOk} />
        </div>
      </div>
    </div>
  );
}
