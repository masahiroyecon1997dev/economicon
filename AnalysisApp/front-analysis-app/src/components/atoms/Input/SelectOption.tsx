type SelectOptionType = {
  value: string;
  children: string;
}

export function SelectOption({ value, children }: SelectOptionType) {
  return (
    <option value={value}>{children}</option>
  )
}
