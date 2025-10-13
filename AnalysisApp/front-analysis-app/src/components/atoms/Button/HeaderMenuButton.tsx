import { FiChevronDown } from "react-icons/fi";

type HeaderMenuButtonProps = {
  children: string;
  clickEvent: () => void;
};

export function HeaderMenuButton({
  children,
  clickEvent,
}: HeaderMenuButtonProps) {
  return (
    <button
      className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-white/10 transition-colors"
      onClick={() => clickEvent()}
    >
      <span>{children}</span>
      <FiChevronDown />
    </button>
  );
}
