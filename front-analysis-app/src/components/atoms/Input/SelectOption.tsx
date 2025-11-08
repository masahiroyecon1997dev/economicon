type SelectOptionType = {
  value: string;
  children: string;
}

export const SelectOption = ({ value, children }: SelectOptionType) => {
  return (
    <option value={value}>{children}</option>
  )
}
