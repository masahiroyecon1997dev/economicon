import { HEADER_MENU_HEIGHT, TABLE_TAB_HEIGHT } from "../../../common/constant";
import type { TableInfosType } from "../../../types/stateTypes";
import { MainTable } from "../Table/MainTable";

type MainPanelProps = {
  tableInfos: TableInfosType;
};

export function MainPanel({ tableInfos }: MainPanelProps) {

  return (
    <main className="flex-1 overflow-y-auto bg-brand-secondary p-8">
      <div
        className="max-w-full mx-auto"
        style={{
          height: `calc(100vh - ${HEADER_MENU_HEIGHT}px - ${TABLE_TAB_HEIGHT}px)`,
        }}
      >
        {tableInfos.map((table, index) => (
          <MainTable key={index} tableInfo={table}></MainTable>
        ))}
      </div>
    </main>
  );
}
