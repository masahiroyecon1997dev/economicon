import { X } from "lucide-react";

type ModalCloseButtonProps = {
  close: () => void;
}

export const ModalCloseButton = ({ close }: ModalCloseButtonProps) => {
  return (
    <button className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center" onClick={() => close()}>
      <X size={24} />
    </button>
  )
}
