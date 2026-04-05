import { beforeEach, describe, expect, it } from "vitest";
import type { TableInfoType } from "../types/commonTypes";
import { useTableChunkStore } from "./tableChunkStore";
import { useTableInfosStore } from "./tableInfos";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const makeInfo = (
  tableName: string,
  overrides: Partial<TableInfoType> = {},
): TableInfoType => ({
  tableName,
  columnList: [{ name: "id", type: "Int64" }],
  totalRows: 10,
  isActive: false,
  ...overrides,
});

beforeEach(() => {
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  // チャンクキャッシュも初期化
  useTableChunkStore.setState({ _cache: new Map(), versions: {} });
});

// ---------------------------------------------------------------------------
// addTableInfo
// ---------------------------------------------------------------------------
describe("useTableInfosStore.addTableInfo", () => {
  it("test_addTableInfo_firstTable_becomesActive", () => {
    const { addTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(1);
    expect(state.tableInfos[0].isActive).toBe(true);
    expect(state.activeTableName).toBe("tableA");
  });

  it("test_addTableInfo_secondTable_deactivatesPrevious", () => {
    const { addTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    addTableInfo(makeInfo("tableB"));

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(2);
    expect(state.tableInfos[0].isActive).toBe(false);
    expect(state.tableInfos[1].isActive).toBe(true);
    expect(state.activeTableName).toBe("tableB");
  });

  it("test_addTableInfo_multipleTablesOnlyOneActive", () => {
    const { addTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("t1"));
    addTableInfo(makeInfo("t2"));
    addTableInfo(makeInfo("t3"));

    const actives = useTableInfosStore
      .getState()
      .tableInfos.filter((i) => i.isActive);
    expect(actives).toHaveLength(1);
    expect(actives[0].tableName).toBe("t3");
  });
});

// ---------------------------------------------------------------------------
// removeTableInfo
// ---------------------------------------------------------------------------
describe("useTableInfosStore.removeTableInfo", () => {
  it("test_removeTableInfo_nonExistentTable_returnsEmptyUpdate", () => {
    const { addTableInfo, removeTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    removeTableInfo("nonExistent");

    expect(useTableInfosStore.getState().tableInfos).toHaveLength(1);
  });

  it("test_removeTableInfo_inactiveTable_doesNotChangeActive", () => {
    const { addTableInfo, removeTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    addTableInfo(makeInfo("tableB")); // B がアクティブ

    removeTableInfo("tableA"); // 非アクティブな A を削除

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(1);
    expect(state.activeTableName).toBe("tableB");
    expect(state.tableInfos[0].isActive).toBe(true);
  });

  it("test_removeTableInfo_activeTable_activatesNeighbor", () => {
    const { addTableInfo, removeTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    addTableInfo(makeInfo("tableB"));
    addTableInfo(makeInfo("tableC")); // C がアクティブ

    removeTableInfo("tableC"); // アクティブな C を削除

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(2);
    // 削除後は最終インデックス側（tableB）がアクティブ
    expect(state.activeTableName).toBe("tableB");
  });

  it("test_removeTableInfo_firstActiveTable_activatesNextTable", () => {
    const { addTableInfo, activateTableInfo, removeTableInfo } =
      useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    addTableInfo(makeInfo("tableB"));
    addTableInfo(makeInfo("tableC"));

    activateTableInfo("tableA"); // A をアクティブに切り替え
    removeTableInfo("tableA"); // index=0 のアクティブなテーブルを削除

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(2);
    // Math.min(0, 1)=0 → filtered[0]=tableB がアクティブになる
    expect(state.activeTableName).toBe("tableB");
    expect(
      state.tableInfos.find((i) => i.tableName === "tableB")?.isActive,
    ).toBe(true);
  });

  it("test_removeTableInfo_lastTable_clearsActiveTableName", () => {
    const { addTableInfo, removeTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));

    removeTableInfo("tableA");

    const state = useTableInfosStore.getState();
    expect(state.tableInfos).toHaveLength(0);
    expect(state.activeTableName).toBeNull();
  });

  it("test_removeTableInfo_clearsCacheForRemovedTable", () => {
    const { addTableInfo, removeTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));

    // チャンクを事前にキャッシュ
    useTableChunkStore.getState().setChunk("tableA", 0, new Uint8Array([1, 2, 3]));
    expect(useTableChunkStore.getState().hasChunk("tableA", 0)).toBe(true);

    removeTableInfo("tableA");

    // テーブル削除後はキャッシュも消えているはず
    expect(useTableChunkStore.getState().hasChunk("tableA", 0)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// updateTableInfo
// ---------------------------------------------------------------------------
describe("useTableInfosStore.updateTableInfo", () => {
  it("test_updateTableInfo_updatesMatchingRecord", () => {
    const { addTableInfo, updateTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA", { totalRows: 5 }));

    const updated = makeInfo("tableA", { totalRows: 50, isActive: true });
    updateTableInfo("tableA", updated);

    const info = useTableInfosStore
      .getState()
      .tableInfos.find((i) => i.tableName === "tableA");
    expect(info?.totalRows).toBe(50);
  });

  it("test_updateTableInfo_unknownTable_doesNothing", () => {
    const { addTableInfo, updateTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    updateTableInfo("nonExistent", makeInfo("nonExistent"));

    expect(useTableInfosStore.getState().tableInfos).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// activateTableInfo
// ---------------------------------------------------------------------------
describe("useTableInfosStore.activateTableInfo", () => {
  it("test_activateTableInfo_setsCorrectTableAsActive", () => {
    const { addTableInfo, activateTableInfo } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));
    addTableInfo(makeInfo("tableB")); // B がアクティブ

    activateTableInfo("tableA");

    const state = useTableInfosStore.getState();
    expect(state.activeTableName).toBe("tableA");
    expect(
      state.tableInfos.find((i) => i.tableName === "tableA")?.isActive,
    ).toBe(true);
    expect(
      state.tableInfos.find((i) => i.tableName === "tableB")?.isActive,
    ).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// invalidateTable
// ---------------------------------------------------------------------------
describe("useTableInfosStore.invalidateTable", () => {
  it("test_invalidateTable_updatesColumnList", () => {
    const { addTableInfo, invalidateTable } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA"));

    const newColumns = [
      { name: "id", type: "Int64" },
      { name: "name", type: "String" },
    ];
    invalidateTable("tableA", { columnList: newColumns });

    const info = useTableInfosStore
      .getState()
      .tableInfos.find((i) => i.tableName === "tableA");
    expect(info?.columnList).toEqual(newColumns);
  });

  it("test_invalidateTable_updatesTotalRows", () => {
    const { addTableInfo, invalidateTable } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA", { totalRows: 10 }));

    invalidateTable("tableA", { totalRows: 999 });

    const info = useTableInfosStore
      .getState()
      .tableInfos.find((i) => i.tableName === "tableA");
    expect(info?.totalRows).toBe(999);
  });

  it("test_invalidateTable_partialUpdate_doesNotClearOtherFields", () => {
    const { addTableInfo, invalidateTable } = useTableInfosStore.getState();
    addTableInfo(makeInfo("tableA", { totalRows: 42 }));

    invalidateTable("tableA", { columnList: [] });

    const info = useTableInfosStore
      .getState()
      .tableInfos.find((i) => i.tableName === "tableA");
    expect(info?.totalRows).toBe(42);
    expect(info?.columnList).toEqual([]);
  });
});
