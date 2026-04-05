import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../api/endpoints";
import { useTableChunkStore } from "../stores/tableChunkStore";
import { useTableInfosStore } from "../stores/tableInfos";
import type { ColumnType } from "../types/commonTypes";
import { useDragColumnReorder } from "./useDragColumnReorder";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockMoveColumn = vi.fn();

const COLUMNS: ColumnType[] = [
  { name: "colA", type: "String" },
  { name: "colB", type: "Int64" },
  { name: "colC", type: "Float64" },
];

const makeDragStart = (id: string): DragStartEvent =>
  ({
    active: {
      id,
      data: { current: {} },
      rect: { current: { initial: null, translated: null } },
    },
  }) as unknown as DragStartEvent;

const makeDragEnd = (activeId: string, overId: string | null): DragEndEvent =>
  ({
    active: {
      id: activeId,
      data: { current: {} },
      rect: { current: { initial: null, translated: null } },
    },
    over:
      overId != null
        ? {
            id: overId,
            data: { current: {} },
            rect: {
              x: 0,
              y: 0,
              width: 0,
              height: 0,
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
            },
          }
        : null,
    delta: { x: 0, y: 0 },
    activatorEvent: new Event("pointerdown"),
    collisions: [],
  }) as unknown as DragEndEvent;

beforeEach(() => {
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    moveColumn: mockMoveColumn,
  } as never);
  mockMoveColumn.mockReset();
  useTableInfosStore.setState({ tableInfos: [], activeTableName: null });
  useTableChunkStore.setState({ _cache: new Map(), versions: {} });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useDragColumnReorder", () => {
  describe("onDragStart", () => {
    it("test_onDragStart_setsActiveColumnId", () => {
      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      act(() => {
        result.current.onDragStart(makeDragStart("colA"));
      });

      expect(result.current.activeColumnId).toBe("colA");
    });

    it("test_onDragStart_clearsDragErrorKey", () => {
      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      // まずエラーを発生させる
      mockMoveColumn.mockResolvedValueOnce({ code: "NG" });
      act(() => {
        result.current.onDragStart(makeDragStart("colA"));
      });

      // dragErrorKey がクリアされていること
      expect(result.current.dragErrorKey).toBeNull();
    });
  });

  describe("onDragEnd", () => {
    it("test_onDragEnd_noOver_doesNotCallAPI", async () => {
      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", null));
      });

      expect(mockMoveColumn).not.toHaveBeenCalled();
    });

    it("test_onDragEnd_sameId_doesNotCallAPI", async () => {
      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", "colA"));
      });

      expect(mockMoveColumn).not.toHaveBeenCalled();
    });

    it("test_onDragEnd_success_callsMoveColumnAPI", async () => {
      mockMoveColumn.mockResolvedValueOnce({ code: "OK" });

      // tableA を store に追加して invalidateTable が動くようにする
      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: COLUMNS,
            totalRows: 3,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", "colC"));
      });

      // colA を末尾の colC 位置へ移動 → anchorColumn は存在しない (null)
      expect(mockMoveColumn).toHaveBeenCalledWith({
        tableName: "tableA",
        columnName: "colA",
        anchorColumnName: null,
      });
      expect(result.current.dragErrorKey).toBeNull();
    });

    it("test_onDragEnd_apiReturnsNG_setsErrorKey", async () => {
      mockMoveColumn.mockResolvedValueOnce({ code: "NG" });

      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: COLUMNS,
            totalRows: 3,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", "colC"));
      });

      expect(result.current.dragErrorKey).toBe("Table.MoveColumnError");
    });

    it("test_onDragEnd_apiThrows_setsErrorKey", async () => {
      mockMoveColumn.mockRejectedValueOnce(new Error("network error"));

      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: COLUMNS,
            totalRows: 3,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", "colC"));
      });

      expect(result.current.dragErrorKey).toBe("Table.MoveColumnError");
    });

    it("test_onDragEnd_unknownColumnId_doesNotCallAPI", async () => {
      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("nonExistent", "colB"));
      });

      expect(mockMoveColumn).not.toHaveBeenCalled();
    });
  });

  describe("clearDragError", () => {
    it("test_clearDragError_clearsDragErrorKey", async () => {
      mockMoveColumn.mockResolvedValueOnce({ code: "NG" });

      useTableInfosStore.setState({
        tableInfos: [
          {
            tableName: "tableA",
            columnList: COLUMNS,
            totalRows: 3,
            isActive: true,
          },
        ],
        activeTableName: "tableA",
      });

      const { result } = renderHook(() =>
        useDragColumnReorder({ tableName: "tableA", columnList: COLUMNS }),
      );

      await act(async () => {
        await result.current.onDragEnd(makeDragEnd("colA", "colC"));
      });
      expect(result.current.dragErrorKey).toBe("Table.MoveColumnError");

      act(() => {
        result.current.clearDragError();
      });

      expect(result.current.dragErrorKey).toBeNull();
    });
  });
});
