import { useEffect, useState } from 'react';

import { useErrorDialogStore } from '../../../stores/useErrorDialogStore';
import { ErrorModalFooter } from './ErrorModalFooter';
import { ModalHeader } from './ModalHeader';

export function ErrorDialog() {
  const { isOpen, title, message, closeErrorDialog } = useErrorDialogStore();
  const [isModalBlock, setIsModalBlock] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      // モーダルを即座に表示
      setIsModalBlock(true);
    } else {
      // フェードアウトアニメーション用の遅延
      const timeout = setTimeout(() => {
        setIsModalBlock(false);
      }, 300); // アニメーション時間を短縮

      return () => clearTimeout(timeout);
    }
  }, [isOpen]);

  const handleOk = () => {
    closeErrorDialog();
  };

  const handleClose = () => {
    closeErrorDialog();
  };

  // モーダルが開いていない かつ ブロック状態でもない場合は何も表示しない
  if (!isOpen && !isModalBlock) {
    return null;
  }

  return (
    <div
      className={`fixed inset-0 z-50 justify-center items-center overflow-y-auto overflow-x-hidden w-full md:inset-0 bg-gray-900/50 ${isModalBlock ? 'flex' : 'hidden'
        }`}
    >
      <div
        className={`relative p-4 w-full max-w-md max-h-full transform transition-all duration-300 ${isOpen ? 'animate-fade-in-down opacity-100' : 'animate-fade-out-up opacity-0'
          }`}
      >
        <div className="relative bg-white rounded-lg shadow">
          <ModalHeader close={handleClose}>{title}</ModalHeader>
          <div className="p-4 md:p-5">
            <p className="text-sm text-gray-900 whitespace-pre-wrap">
              {message}
            </p>
          </div>
          <ErrorModalFooter onOk={handleOk} />
        </div>
      </div>
    </div>
  );
}
