import { cn } from "@/lib/utils/helpers";
import { openExplainerDialog } from "@/stores/explainerDialog";
import { type ComponentPropsWithoutRef } from "react";

type ExplainerButtonProps = ComponentPropsWithoutRef<"button"> & {
  explainerKey: string;
};

export const ExplainerButton = ({
  explainerKey,
  className,
  onClick,
  type = "button",
  ...props
}: ExplainerButtonProps) => {
  return (
    <button
      type={type}
      className={cn(
        "text-gray-400 transition-colors hover:text-brand-accent",
        className,
      )}
      onClick={(event) => {
        openExplainerDialog(
          explainerKey,
          event.currentTarget.getBoundingClientRect(),
        );
        onClick?.(event);
      }}
      {...props}
    />
  );
};
