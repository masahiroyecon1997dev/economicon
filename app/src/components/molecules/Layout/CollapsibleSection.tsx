import { cn } from "@/lib/utils/helpers";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

type CollapsibleSectionProps = {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
};

export const CollapsibleSection = ({
  title,
  children,
  defaultOpen = false,
}: CollapsibleSectionProps) => {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border border-border-color rounded-md">
      <button
        type="button"
        className="flex w-full items-center justify-between px-3 py-2 text-sm text-text-main/80 hover:bg-secondary transition-colors rounded-md"
        onClick={() => setOpen((prev) => !prev)}
        data-testid="collapsible-trigger"
      >
        <span>{title}</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 transition-transform text-text-main/60",
            open && "rotate-180",
          )}
        />
      </button>
      {open && (
        <div className="px-3 pb-3 pt-1" data-testid="collapsible-content">
          {children}
        </div>
      )}
    </div>
  );
};
