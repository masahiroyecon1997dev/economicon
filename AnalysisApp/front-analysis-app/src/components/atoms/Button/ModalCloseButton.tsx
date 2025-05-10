import React from "react";

import { IconContext } from "react-icons";
import { MdClose } from "react-icons/md";

type ModalCloseButtonProps = {
  close: () => void;
}

export function ModalCloseButton ({ close }: ModalCloseButtonProps) {
  return (
    <button className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white" onClick={() => close()}>
      <IconContext.Provider value={{ size: '2rem'}}><MdClose/></IconContext.Provider>
    </button>
  )
}
