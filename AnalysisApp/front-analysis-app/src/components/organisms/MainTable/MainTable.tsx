import React from "react";

import { TableInfoType } from "../../../types/commonTypes";

import { MainTableThead } from "../../molecules/MainTableThead/MainTableThead";
import { MainTableTbody } from "../../molecules/MainTableTbody/MainTableTbody";

type MainTableProps = {
  tableInfo: TableInfoType;
};

export function MainTable({ tableInfo }: MainTableProps) {
  return (
    <div>
      <table className="border-separate border-spacing-0 border-l border-r bg-white border-gray-300 table-auto">
        <MainTableThead
          columnNameList={tableInfo.columnNameList}
        ></MainTableThead>
        <MainTableTbody tableData={tableInfo.data}></MainTableTbody>
      </table>
    </div>
  );
}
