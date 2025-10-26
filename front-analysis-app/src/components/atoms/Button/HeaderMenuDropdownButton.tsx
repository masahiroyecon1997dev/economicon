type HeaderMenuDropdownButtonProps = {
  children: string;
  isTop: boolean;
  isBottom: boolean;
  clickEvent: () => void;
};

export function HeaderMenuDropdownButton({
  children,
  isTop,
  isBottom,
  clickEvent,
}: HeaderMenuDropdownButtonProps) {
  return (
    <button
      className={`block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer transition-colors ${
        isTop ? "rounded-t-md" : ""
      } ${isBottom ? "rounded-b-md" : ""}`}
      onClick={() => clickEvent()}
    >
      {children}
    </button>
  );
}
