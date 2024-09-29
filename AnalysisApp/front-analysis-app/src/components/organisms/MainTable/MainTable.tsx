import React from "react";

import { TableInfoType } from "../../../types/commonTypes";

import { MainTableThead } from "../../molecules/MainTableThead/MainTableThead";
import { MainTableTbody } from "../../molecules/MainTableTbody/MainTableTbody";

type MainTableProps = {
  tableInfo: TableInfoType;
};

export function MainTable({ tableInfo }: MainTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="bg-white border border-gray-300">
        <MainTableThead
          columnNameList={tableInfo.columnNameList}
        ></MainTableThead>
        <MainTableTbody tableData={tableInfo.data}></MainTableTbody>
      </table>
    </div>
  );
}
