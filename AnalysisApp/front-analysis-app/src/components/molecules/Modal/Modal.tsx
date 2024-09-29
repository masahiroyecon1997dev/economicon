import React, { ReactNode, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";

import { ModalHeader } from "../../molecules/ModalHeader/ModalHeader";
import { ModalFooter } from "../../molecules/ModalFooter/ModalFooter";

type SaveFileModalProps = {
  isOpenModal: boolean;
  children: ReactNode;
  modalTitle: string;
  submitButtonName: string;
  submit: () => void;
  close: () => void;
};

export function Modal({
  isOpenModal,
  children,
  modalTitle,
  submitButtonName,
  submit,
  close,
}: SaveFileModalProps) {
  const { t } = useTranslation();
  const [isModalBlock, setIsModalblock] = useState<boolean>(false);

  useEffect(() => {
    if (isOpenModal) {
      setIsModalblock(isOpenModal);
    } else {
      setTimeout(() => {
        setIsModalblock(isOpenModal);
      }, 400);
    }
  }, [isOpenModal]);

  return (
    <div
      className={`fixed inset-0 z-50 justify-center items-center overflow-y-auto overflow-x-hidden w-full md:inset-0 bg-gray-900 bg-opacity-50 ${
        isModalBlock ? "flex" : "hidden"
      }`}
    >
      <div
        className={`relative p-4 w-full max-w-2xl max-h-full transform ${
          isOpenModal ? "animate-fade-in-down" : "animate-fade-out-up"
        }`}
      >
        <div className="relative bg-white rounded-lg shadow dark:bg-gray-700">
          <ModalHeader close={() => close()}>{modalTitle}</ModalHeader>
          <div className="">{children}</div>
          <ModalFooter close={() => close()} submit={() => submit()}>
            {submitButtonName}
          </ModalFooter>
        </div>
      </div>
    </div>
  );
}
