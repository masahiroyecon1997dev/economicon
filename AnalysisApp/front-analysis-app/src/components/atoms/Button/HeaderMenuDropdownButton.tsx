type HeaderMenuDropdownButtonProps = {
  children: string;
  clickEvent: () => void;
};

export function HeaderMenuDropdownButton({
  children,
  clickEvent,
}: HeaderMenuDropdownButtonProps) {
  return (
    <button
      className="block w-32 px-4 py-2 hover:bg-brand-primary-light text-left whitespace-nowrap"
      onClick={() => clickEvent()}
    >
      {children}
    </button>
  );
}
