import React from "react";

import { MainTableTh } from "../../atoms/MainTableTh/MainTableTh";

type MainTableTheadProps = {
  columnNameList: string[];
};

export function MainTableThead({ columnNameList }: MainTableTheadProps) {
  return (
    <thead>
      <tr>
        {columnNameList.map((columnName, i) => (
          <MainTableTh key={i}>{columnName}</MainTableTh>
        ))}
      </tr>
    </thead>
  );
}
