import { faChevronDown } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type HeaderMenuButtonProps = {
  children: string;
  clickEvent: () => void;
};

export const HeaderMenuButton = ({
  children,
  clickEvent,
}: HeaderMenuButtonProps) => {
  return (
    <button
      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-white/10 transition-colors"
      onClick={() => clickEvent()}
    >
      <span>{children}</span>
      <FontAwesomeIcon icon={faChevronDown} />
    </button>
  );
}
