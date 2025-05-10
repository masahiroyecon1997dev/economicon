import React, { ChangeEvent } from 'react';
import { TableDataCellType } from '../../../types/commonTypes';

type TableInputTextProps = {
  value: TableDataCellType;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
};

export function TableInputText({ value, onChange, onBlur }: TableInputTextProps) {
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
