import { cn } from "../../../common/utils";

type SubmitButtonProps = {
  children: string;
  submit: () => void;
  className?: string;
};

export const SubmitButton = ({ children, submit, className }: SubmitButtonProps) => {
  return (
    <button
      onClick={submit}
      className={cn(
        "rounded-md bg-brand-accent px-6 py-2.5 text-sm font-semibold text-white shadow-sm",
        "hover:bg-brand-accent/90 transition-colors cursor-pointer",
        "focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-brand-accent",
        className
      )}
    >
      {children}
    </button>
  );
}
