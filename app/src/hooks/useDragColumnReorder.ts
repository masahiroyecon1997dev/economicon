/**
 * 列ヘッダーのドラッグ&ドロップによる列移動 hook
 *
 * - 楽観的更新: drop 直後にローカルの columnList を新順序で反映
 * - API 失敗時: 元の columnList にロールバック
 * - anchorColumnName: 移動先列の「直前」挿入（before セマンティクス）
 */
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { useCallback, useState } from "react";
import { getEconomiconAppAPI } from "../api/endpoints";
import { useTableInfosStore } from "../stores/tableInfos";
import type { ColumnType } from "../types/commonTypes";

type UseDragColumnReorderOptions = {
  tableName: string;
  columnList: ColumnType[];
};

type UseDragColumnReorderReturn = {
  activeColumnId: string | null;
  /** i18n キー: "Table.MoveColumnError" */
  dragErrorKey: string | null;
  onDragStart: (event: DragStartEvent) => void;
  onDragEnd: (event: DragEndEvent) => Promise<void>;
  clearDragError: () => void;
};

export const useDragColumnReorder = ({
  tableName,
  columnList,
}: UseDragColumnReorderOptions): UseDragColumnReorderReturn => {
  const [activeColumnId, setActiveColumnId] = useState<string | null>(null);
  const [dragErrorKey, setDragErrorKey] = useState<string | null>(null);
  const invalidateTable = useTableInfosStore((s) => s.invalidateTable);

  const onDragStart = useCallback((event: DragStartEvent) => {
    setActiveColumnId(String(event.active.id));
    setDragErrorKey(null);
  }, []);

  const onDragEnd = useCallback(
    async (event: DragEndEvent) => {
      setActiveColumnId(null);
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const oldIndex = columnList.findIndex((c) => c.name === active.id);
      const newIndex = columnList.findIndex((c) => c.name === over.id);
      if (oldIndex === -1 || newIndex === -1) return;

      // 楽観的更新: 即座に新しい列順をローカルに反映
      const newColumnList = arrayMove(columnList, oldIndex, newIndex);
      invalidateTable(tableName, { columnList: newColumnList });

      // anchorColumnName の導出（before セマンティクス）
      // newIndex 位置に挿入した後の newIndex+1 が anchor
      const anchorColumn = newColumnList[newIndex + 1] ?? null;

      try {
        const response = await getEconomiconAppAPI().moveColumn({
          tableName,
          columnName: String(active.id),
          anchorColumnName: anchorColumn?.name ?? null,
        });

        if (response.code !== "OK") {
          // API は NG を返した（例外でなく response.code チェック）
          invalidateTable(tableName, { columnList });
          setDragErrorKey("Table.MoveColumnError");
        }
      } catch {
        // 通信エラー: ロールバック
        invalidateTable(tableName, { columnList });
        setDragErrorKey("Table.MoveColumnError");
      }
    },
    [tableName, columnList, invalidateTable],
  );

  const clearDragError = useCallback(() => setDragErrorKey(null), []);

  return {
    activeColumnId,
    dragErrorKey,
    onDragStart,
    onDragEnd,
    clearDragError,
  };
};
