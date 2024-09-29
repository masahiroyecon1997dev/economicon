import React, { ChangeEvent } from "react";

import { SelectOption } from "../../atoms/SelectOption/SelectOption";
import { SelectListType } from "../../../types/commonTypes";

type SelectType = {
  optionList: SelectListType;
  selectFunc: (event: ChangeEvent<HTMLSelectElement>) => void;
};

export function Select({ optionList, selectFunc }: SelectType) {
  return (
    <select
      className="h-12 border border-gray-300 text-gray-600 text-base rounded-lg block w-full py-2.5 px-4 focus:outline-none"
      onChange={(event) => selectFunc(event)}
    >
      {optionList.map((optionObj, i) => (
        <SelectOption key={i} value={optionObj.value}>
          {optionObj.name}
        </SelectOption>
      ))}
    </select>
  );
}
