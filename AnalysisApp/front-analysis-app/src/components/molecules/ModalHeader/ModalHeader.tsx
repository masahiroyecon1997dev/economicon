import React from "react";

import { ModalHeaderTitle } from "../../atoms/ModalHeaderTitle/ModalHeaderTitle";
import { ModalCloseButton } from "../../atoms/ModalCloseButton/ModalCloseButton";

type ModalHeaderProps = {
  children: string;
  close: () => void;
};

export function ModalHeader({ children, close }: ModalHeaderProps) {
  return (
    <div className="flex items-center justify-between p-4 md:p-5 border-b border-b-gray-300 rounded-t dark:border-gray-600">
      <ModalHeaderTitle>{children}</ModalHeaderTitle>
      <ModalCloseButton close={() => close()}></ModalCloseButton>
    </div>
  );
}
