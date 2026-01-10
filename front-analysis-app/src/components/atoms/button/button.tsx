import { cn } from "../../../common/utils";

type ButtonProps = {
  children: string;
  onClick: () => void;
  variant?: "cancel" | "submit";
  className?: string;
};

export const Button = ({ children, onClick, variant = "submit", className }: ButtonProps) => {
  const baseStyles = "rounded-md px-6 py-2.5 text-sm font-semibold transition-colors cursor-pointer";

  const variantStyles = {
    cancel: cn(
      "text-main dark:text-gray-300",
      "bg-white dark:bg-gray-700 border border-border-color dark:border-gray-600",
      "hover:bg-gray-50 dark:hover:bg-gray-600"
    ),
    submit: cn(
      "bg-brand-accent text-white shadow-sm",
      "hover:bg-brand-accent/90",
      "focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-brand-accent"
    ),
  };

  return (
    <button
      onClick={onClick}
      className={cn(baseStyles, variantStyles[variant], className)}
      aria-label={variant}
    >
      {children}
    </button>
  );
}
