type FileFilterButtonProps = {
  children: string;
  isActive?: boolean;
  onClick: () => void;
};

export const FileFilterButton = ({ children, isActive = false, onClick }: FileFilterButtonProps) => {
  return (
    <button
      onClick={onClick}
      className={`flex h-9 shrink-0 items-center justify-center gap-x-2 rounded-full px-4 text-sm font-medium transition-colors ${isActive
        ? 'bg-primary/10 dark:bg-primary/20 text-primary hover:bg-primary/20 dark:hover:bg-primary/30'
        : 'bg-transparent text-black/60 dark:text-white/60 hover:bg-primary/10 dark:hover:bg-primary/20 hover:text-primary dark:hover:text-primary'
        }`}
    >
      <span>{children}</span>
      {isActive && (
        <span className="material-symbols-outlined text-base">expand_more</span>
      )}
    </button>
  );
}
