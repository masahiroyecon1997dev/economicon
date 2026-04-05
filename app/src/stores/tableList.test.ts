import { beforeEach, describe, expect, it } from "vitest";
import { useTableListStore } from "./tableList";

beforeEach(() => {
  useTableListStore.setState({ tableList: [] });
});

describe("useTableListStore", () => {
  describe("setTableList", () => {
    it("test_setTableList_replacesEntireList", () => {
      const { setTableList } = useTableListStore.getState();
      setTableList(["tableA", "tableB"]);

      const { tableList } = useTableListStore.getState();
      expect(tableList).toEqual(["tableA", "tableB"]);
    });

    it("test_setTableList_emptyArray_clearsAll", () => {
      useTableListStore.setState({ tableList: ["tableA"] });
      const { setTableList } = useTableListStore.getState();
      setTableList([]);

      expect(useTableListStore.getState().tableList).toEqual([]);
    });
  });

  describe("addTableName", () => {
    it("test_addTableName_appendsToEmptyList", () => {
      const { addTableName } = useTableListStore.getState();
      addTableName("newTable");

      expect(useTableListStore.getState().tableList).toEqual(["newTable"]);
    });

    it("test_addTableName_appendsToExistingList", () => {
      useTableListStore.setState({ tableList: ["existing"] });
      const { addTableName } = useTableListStore.getState();
      addTableName("newTable");

      expect(useTableListStore.getState().tableList).toEqual([
        "existing",
        "newTable",
      ]);
    });

    it("test_addTableName_allowsDuplicateNames", () => {
      const { addTableName } = useTableListStore.getState();
      addTableName("dup");
      addTableName("dup");

      expect(useTableListStore.getState().tableList).toHaveLength(2);
    });
  });

  describe("removeTableName", () => {
    it("test_removeTableName_removesExistingEntry", () => {
      useTableListStore.setState({ tableList: ["tableA", "tableB"] });
      const { removeTableName } = useTableListStore.getState();
      removeTableName("tableA");

      expect(useTableListStore.getState().tableList).toEqual(["tableB"]);
    });

    it("test_removeTableName_unknownName_doesNothing", () => {
      useTableListStore.setState({ tableList: ["tableA"] });
      const { removeTableName } = useTableListStore.getState();
      removeTableName("nonExistent");

      expect(useTableListStore.getState().tableList).toEqual(["tableA"]);
    });

    it("test_removeTableName_allOccurrencesRemoved_whenDuplicate", () => {
      useTableListStore.setState({ tableList: ["dup", "dup"] });
      const { removeTableName } = useTableListStore.getState();
      removeTableName("dup");

      // 実装は filter のため同名を全件削除する
      expect(useTableListStore.getState().tableList).toEqual([]);
    });
  });
});
