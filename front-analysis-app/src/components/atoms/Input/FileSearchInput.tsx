import { faMagnifyingGlass } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

type FileSearchInputProps = {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
};

export const FileSearchInput = ({ placeholder, value, onChange }: FileSearchInputProps) => {
  return (
    <div className="w-full relative border-brand-border">
      <FontAwesomeIcon
        icon={faMagnifyingGlass}
        className="absolute left-3 top-1/2 -translate-y-1/2 text-black/40 z-10"
      />
      <input
        className="w-full rounded-lg border border-solid bg-transparent py-2 pl-10 pr-4 text-black placeholder:text-black/40 focus:ring-primary/50 focus:outline-none focus:border-brand-primary transition-colors min-w-0"
        placeholder={placeholder}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
