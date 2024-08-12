import React from 'react';

import { TableDataType } from '../../../types/commonTypes';

import { MainTableTd } from '../../atoms/MainTableTd/MainTableTd';

type MainTableTbodyProps = {
  tableData: TableDataType;
}

export function MainTableTbody({ tableData }: MainTableTbodyProps) {
  return (
    <tbody>
      {tableData?.map((row, i) => (
        <tr key={i}>
          {Object.values(row).map((cell, i) => (
            <MainTableTd key={i}>{cell?.toString() ? cell.toString() : ''}</MainTableTd>
          ))}
        </tr>
      ))}
    </tbody>
  )
}
