import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type ModalCloseButtonProps = {
  close: () => void;
}

export const ModalCloseButton = ({ close }: ModalCloseButtonProps) => {
  return (
    <button className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center" onClick={() => close()}>
      <FontAwesomeIcon icon={faXmark} className="text-2xl" />
    </button>
  )
}
