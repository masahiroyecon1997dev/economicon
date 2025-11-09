import type { ChangeEvent } from 'react';
import type { TableDataCellType } from '../../../types/commonTypes';

type TableInputTextProps = {
  value: TableDataCellType;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
};

export const TableInputText = ({ value, onChange, onBlur }: TableInputTextProps) => {
  return (
    <input
      type="text"
      className="w-full border rounded p-1"
      value={value?.toString()}
      onChange={onChange}
      onBlur={onBlur}
      autoFocus
    />
  );
}
