import React, { ChangeEvent } from 'react';

import { SelectOption } from '../../atoms/Input/SelectOption';
import { SelectListType } from '../../../types/commonTypes';

type SelectType = {
  optionList: SelectListType;
  selectFunc: (event: ChangeEvent<HTMLSelectElement>) => void;
};

export function Select({ optionList, selectFunc }: SelectType) {
  return (
    <select
      className="h-9 border border-gray-300 text-gray-600 text-sm rounded-lg block w-full py-1 px-4 focus:outline-none"
      onChange={event => selectFunc(event)}
    >
      {optionList.map((optionObj, i) => (
        <SelectOption key={i} value={optionObj.value}>
          {optionObj.name}
        </SelectOption>
      ))}
    </select>
  );
}
