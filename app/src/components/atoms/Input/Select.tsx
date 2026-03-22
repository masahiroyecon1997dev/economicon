import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import { type ReactNode } from "react";
import { cn } from "../../../lib/utils/helpers";

type SelectProps = {
  value: string;
  onValueChange: (value: string) => void;
  children: ReactNode;
  error?: string;
  className?: string;
  id?: string;
  name?: string;
  placeholder?: string;
  disabled?: boolean;
};

export const Select = ({
  value,
  onValueChange,
  children,
  error = "",
  className,
  id,
  name,
  placeholder,
  disabled = false,
}: SelectProps) => {
  return (
    <SelectPrimitive.Root name={name} value={value} onValueChange={onValueChange} disabled={disabled}>
      <SelectPrimitive.Trigger
        id={id}
        name={name}
        className={cn(
          "flex w-full items-center justify-between px-2.5 py-1.5 text-sm font-normal text-gray-900 bg-white border rounded-md shadow-sm",
          "focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200 cursor-pointer",
          "disabled:cursor-not-allowed disabled:opacity-50",
          error
            ? "border-red-500 focus:ring-red-500 focus:border-red-500"
            : "border-gray-300 focus:ring-gray-700 focus:border-gray-700 hover:border-gray-400",
          className
        )}
      >
        <SelectPrimitive.Value placeholder={placeholder} />
        <SelectPrimitive.Icon>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          className={cn(
            "relative z-50 min-w-32 overflow-hidden rounded-md border border-gray-200 bg-white text-gray-900 shadow-md",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
            "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2",
            "data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
            "min-w-(--radix-select-trigger-width)"
          )}
          position="popper"
          sideOffset={4}
        >
          <SelectPrimitive.Viewport className="p-1">
            {children}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  );
};

type SelectItemProps = {
  value: string;
  children: string;
  className?: string;
  disabled?: boolean;
};

export const SelectItem = ({
  value,
  children,
  className,
  disabled = false,
}: SelectItemProps) => {
  return (
    <SelectPrimitive.Item
      value={value}
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none",
        "focus:bg-gray-100 focus:text-gray-900",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        className
      )}
      disabled={disabled}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <Check className="h-4 w-4" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
};
