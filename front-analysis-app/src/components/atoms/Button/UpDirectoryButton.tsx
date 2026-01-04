import { faArrowUp } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type UpDirectoryButtonProps = {
  onClick: () => void;
  title: string;
};

export const UpDirectoryButton = ({ onClick, title }: UpDirectoryButtonProps) => {
  return (
    <button
      onClick={onClick}
      className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
      title={title}
    >
      <FontAwesomeIcon icon={faArrowUp} className="text-base" />
    </button>
  );
}
