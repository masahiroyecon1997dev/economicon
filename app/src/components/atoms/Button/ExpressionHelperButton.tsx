import { cn } from "../../../lib/utils/helpers";

type ExpressionHelperButtonProps = {
  onClick: () => void;
  children: React.ReactNode;
  title?: string;
  className?: string;
  disabled?: boolean;
};

export const ExpressionHelperButton = ({
  onClick,
  children,
  title,
  className,
  disabled,
}: ExpressionHelperButtonProps) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "h-8 px-3 flex items-center justify-center rounded",
        "bg-white dark:bg-neutral-700",
        "border border-border-color",
        "text-brand-text-main dark:text-neutral-200",
        "hover:bg-neutral-100 hover:border-accent",
        "transition-colors shadow-sm",
        "font-mono text-xs font-medium",
        className,
      )}
      title={title}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
