import { cn } from "../../../common/utils";

type HeaderMenuDropdownButtonProps = {
  children: string;
  isTop: boolean;
  isBottom: boolean;
  clickEvent: () => void;
  className?: string;
};

export const HeaderMenuDropdownButton = ({
  children,
  isTop,
  isBottom,
  clickEvent,
  className,
}: HeaderMenuDropdownButtonProps) => {
  return (
    <button
      className={cn(
        "block w-full text-left px-4 py-2 text-sm text-gray-700",
        "hover:bg-gray-100 cursor-pointer transition-colors",
        isTop && "rounded-t-md",
        isBottom && "rounded-b-md",
        className
      )}
      onClick={() => clickEvent()}
    >
      {children}
    </button>
  );
}
