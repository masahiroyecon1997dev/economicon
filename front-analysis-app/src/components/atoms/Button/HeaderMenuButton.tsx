import { ChevronDown } from "lucide-react";
import { cn } from "../../../common/utils";

type HeaderMenuButtonProps = {
  children: string;
  clickEvent: () => void;
  className?: string;
};

export const HeaderMenuButton = ({
  children,
  clickEvent,
  className,
}: HeaderMenuButtonProps) => {
  return (
    <button
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
        "hover:bg-white/10 transition-colors",
        className
      )}
      onClick={() => clickEvent()}
    >
      <span>{children}</span>
      <ChevronDown size={16} />
    </button>
  );
}
