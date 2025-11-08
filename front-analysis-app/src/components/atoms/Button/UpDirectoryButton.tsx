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
      className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30 transition-colors"
      title={title}
    >
      <FontAwesomeIcon icon={faArrowUp} className="text-xl" />
    </button>
  );
}
