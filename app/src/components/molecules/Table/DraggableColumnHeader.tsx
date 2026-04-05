/**
 * ドラッグ可能な列ヘッダー
 *
 * - useSortable で列ヘッダーをドラッグ対象にする
 * - ドラッグ中: 半透明 + cursor-grabbing
 * - GripVertical アイコンをホバー時に表示してドラッグ可能であることを示す
 * - 既存の ColumnContextMenu をラップする
 */
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "../../../lib/utils/helpers";

type DraggableColumnHeaderProps = {
  id: string;
  children: ReactNode;
};

export const DraggableColumnHeader = ({
  id,
  children,
}: DraggableColumnHeaderProps) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "flex items-center gap-1 w-full",
        isDragging && "opacity-40",
      )}
    >
      {/* ドラッグハンドル */}
      <div
        {...attributes}
        {...listeners}
        className="shrink-0 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500 dark:text-gray-600 dark:hover:text-gray-400 transition-colors"
        data-testid={`drag-handle-${id}`}
      >
        <GripVertical className="h-3 w-3" />
      </div>
      {children}
    </div>
  );
};
