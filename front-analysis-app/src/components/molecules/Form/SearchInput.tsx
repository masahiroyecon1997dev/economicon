import { Search } from "lucide-react";
import { cn } from "../../../functions/utils";

type SearchInputProps = {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
};

export const SearchInput = ({ placeholder, value, onChange, className }: SearchInputProps) => {
  return (
    <div className={cn("w-full relative border-brand-border", className)}>
      <Search
        className="absolute left-2.5 top-1/2 -translate-y-1/2 text-black/40 z-10"
        size={16}
      />
      <input
        className={cn(
          "w-full rounded-lg border border-solid bg-transparent py-1.5 pl-8 pr-3 text-sm text-black",
          "placeholder:text-black/40 focus:ring-primary/50 focus:outline-none",
          "focus:border-brand-primary transition-colors min-w-0"
        )}
        placeholder={placeholder}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
