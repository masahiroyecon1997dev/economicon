import { cn } from "../../../common/utils";

type SelectOptionType = {
  value: string;
  children: string;
  className?: string;
}

export const SelectOption = ({ value, children, className }: SelectOptionType) => {
  return (
    <option value={value} className={cn(className)}>{children}</option>
  )
}
