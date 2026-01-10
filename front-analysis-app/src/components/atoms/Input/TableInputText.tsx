import type { ChangeEvent } from 'react';
import { cn } from "../../../common/utils";
import type { TableDataCellType } from '../../../types/commonTypes';

type TableInputTextProps = {
  value: TableDataCellType;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
  className?: string;
};

export const TableInputText = ({ value, onChange, onBlur, className }: TableInputTextProps) => {
  return (
    <input
      type="text"
      className={cn("w-full border rounded p-1", className)}
      value={value?.toString()}
      onChange={onChange}
      onBlur={onBlur}
      autoFocus
    />
  );
}
