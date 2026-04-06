import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils/helpers";

type UpDirectoryButtonProps = {
  onClick: () => void;
  title: string;
  className?: string;
};

export const UpDirectoryButton = ({ onClick, title, className }: UpDirectoryButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full",
        "bg-primary/10 text-primary hover:bg-primary/20 transition-colors",
        className
      )}
      title={title}
    >
      <ArrowUp size={16} />
    </button>
  );
}
