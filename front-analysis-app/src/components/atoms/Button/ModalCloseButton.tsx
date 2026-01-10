import { X } from "lucide-react";
import { cn } from "../../../common/utils";

type ModalCloseButtonProps = {
  close: () => void;
  className?: string;
}

export const ModalCloseButton = ({ close, className }: ModalCloseButtonProps) => {
  return (
    <button
      className={cn(
        "text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900",
        "rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center",
        "transition-colors",
        className
      )}
      onClick={() => close()}
    >
      <X size={24} />
    </button>
  )
}
