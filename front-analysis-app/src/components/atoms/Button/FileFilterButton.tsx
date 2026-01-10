import { cn } from "../../../common/utils";

type FileFilterButtonProps = {
  children: string;
  isActive?: boolean;
  onClick: () => void;
  className?: string;
};

export const FileFilterButton = ({ children, isActive = false, onClick, className }: FileFilterButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full px-4 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary/10 text-primary hover:bg-primary/20"
          : "bg-transparent text-black/60 hover:bg-primary/10 hover:text-primary",
        className
      )}
    >
      <span>{children}</span>
      {isActive && (
        <span className="material-symbols-outlined text-base">expand_more</span>
      )}
    </button>
  );
}
