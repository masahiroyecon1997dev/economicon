import { Tooltip } from "@/components/atoms/Tooltip/Tooltip";
import { cn } from "@/lib/utils/helpers";
import { ArrowUp } from "lucide-react";

type UpDirectoryButtonProps = {
  onClick: () => void;
  title: string;
  className?: string;
};

export const UpDirectoryButton = ({
  onClick,
  title,
  className,
}: UpDirectoryButtonProps) => {
  const button = (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full",
        "bg-primary/10 text-primary hover:bg-primary/20 transition-colors",
        className,
      )}
      aria-label={title}
    >
      <ArrowUp size={16} />
    </button>
  );

  return (
    <Tooltip content={title}>
      <span className="inline-flex">{button}</span>
    </Tooltip>
  );
};
