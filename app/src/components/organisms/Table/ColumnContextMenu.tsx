/**
 * 列ヘッダーのコンテキストメニューコンポーネント
 *
 * - 列ヘッダー全体を右クリックすると Radix ContextMenu を開く
 * - sort_asc / sort_desc は直接 API コール（ダイアログなし）
 * - その他の操作は親コンポーネントへ operation イベントを伝達
 */
import * as ContextMenu from "@radix-ui/react-context-menu";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import {
  ArrowDownAZ,
  ArrowUpAZ,
  CopyPlus,
  Dices,
  FileClock,
  Filter,
  FlipHorizontal,
  MoreVertical,
  Sigma,
  Tags,
  Trash2,
} from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils/helpers";
import type { ColumnType } from "@/types/commonTypes";

export type ColumnOperation =
  | "sort_asc"
  | "sort_desc"
  | "rename"
  | "duplicate"
  | "cast"
  | "transform"
  | "addDummy"
  | "addLagLead"
  | "addSimulation"
  | "filter"
  | "delete";

type ColumnContextMenuProps = {
  column: ColumnType;
  onAction: (operation: ColumnOperation) => void;
  children: ReactNode;
};

const menuItemClass = cn(
  "flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm text-gray-700 dark:text-gray-200 outline-none cursor-pointer",
  "data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-gray-700",
  "data-[highlighted]:text-gray-900 dark:data-[highlighted]:text-white",
  "data-disabled:pointer-events-none data-disabled:opacity-40",
);

const destructiveItemClass = cn(
  menuItemClass,
  "text-red-600 data-[highlighted]:bg-red-50 data-[highlighted]:text-red-700",
  "dark:data-[highlighted]:bg-red-950 dark:data-[highlighted]:text-red-400",
);

const contentClass = cn(
  "z-50 min-w-50 rounded-md bg-white dark:bg-gray-800 shadow-lg",
  "border border-gray-200 dark:border-gray-700",
  "data-[state=open]:animate-in data-[state=closed]:animate-out",
  "data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
  "data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
);

// ---------------------------------------------------------------------------
// 共通スロット型: ContextMenu / DropdownMenu 両方と互換
// ---------------------------------------------------------------------------
type MenuSlots = {
  Item: ComponentType<{
    className?: string;
    onSelect?: (event: Event) => void;
    children?: ReactNode;
  }>;
  Group: ComponentType<{ className?: string; children?: ReactNode }>;
  Separator: ComponentType<{ className?: string }>;
  Label: ComponentType<{ className?: string; children?: ReactNode }>;
};

type ColumnMenuItemsProps = MenuSlots & {
  column: ColumnType;
  onAction: (op: ColumnOperation) => void;
};

const ColumnMenuItems = ({
  Item,
  Group,
  Separator,
  Label,
  column,
  onAction,
}: ColumnMenuItemsProps) => {
  const { t } = useTranslation();
  return (
    <>
      {/* ソート */}
      <Group className="p-1">
        <Label className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
          {column.name}
        </Label>
        <Item className={menuItemClass} onSelect={() => onAction("sort_asc")}>
          <ArrowUpAZ className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.SortAsc")}
        </Item>
        <Item className={menuItemClass} onSelect={() => onAction("sort_desc")}>
          <ArrowDownAZ className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.SortDesc")}
        </Item>
      </Group>
      <Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />
      {/* 列編集 */}
      <Group className="p-1">
        <Item className={menuItemClass} onSelect={() => onAction("rename")}>
          <FlipHorizontal className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.Rename")}
        </Item>
        <Item className={menuItemClass} onSelect={() => onAction("duplicate")}>
          <CopyPlus className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.Duplicate")}
        </Item>
      </Group>
      <Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />
      {/* 列追加系 */}
      <Group className="p-1">
        <Item className={menuItemClass} onSelect={() => onAction("cast")}>
          <Sigma className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.Cast")}
        </Item>
        <Item className={menuItemClass} onSelect={() => onAction("transform")}>
          <Sigma className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.Transform")}
        </Item>
        <Item className={menuItemClass} onSelect={() => onAction("addDummy")}>
          <Tags className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.AddDummy")}
        </Item>
        <Item className={menuItemClass} onSelect={() => onAction("addLagLead")}>
          <FileClock className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.AddLagLead")}
        </Item>
        <Item
          className={menuItemClass}
          onSelect={() => onAction("addSimulation")}
        >
          <Dices className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.AddSimulation")}
        </Item>
      </Group>
      <Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />
      {/* フィルタ */}
      <Group className="p-1">
        <Item className={menuItemClass} onSelect={() => onAction("filter")}>
          <Filter className="h-4 w-4 text-gray-500 shrink-0" />
          {t("ColumnMenu.Filter")}
        </Item>
      </Group>
      <Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />
      {/* 削除 */}
      <Group className="p-1">
        <Item
          className={destructiveItemClass}
          onSelect={() => onAction("delete")}
        >
          <Trash2 className="h-4 w-4 shrink-0" />
          {t("ColumnMenu.Delete")}
        </Item>
      </Group>
    </>
  );
};

export const ColumnContextMenu = ({
  column,
  onAction,
  children,
}: ColumnContextMenuProps) => {
  const { t } = useTranslation();

  return (
    <ContextMenu.Root>
      <ContextMenu.Trigger asChild>
        <div className="group flex items-center gap-1.5 min-w-0 w-full h-full">
          {children}
          {/* 縦三点リーダー: ホバー時 or メニュー開放時のみ表示 */}
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button
                type="button"
                className={cn(
                  "ml-auto shrink-0 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity",
                  "hover:bg-gray-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400",
                  "data-[state=open]:opacity-100 data-[state=open]:bg-gray-200",
                )}
                aria-label={t("ColumnMenu.OpenColumnMenu")}
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-3.5 w-3.5 text-gray-500" />
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                side="bottom"
                align="start"
                sideOffset={4}
                className={contentClass}
              >
                <ColumnMenuItems
                  Item={DropdownMenu.Item}
                  Group={DropdownMenu.Group}
                  Separator={DropdownMenu.Separator}
                  Label={DropdownMenu.Label}
                  column={column}
                  onAction={onAction}
                />
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </ContextMenu.Trigger>

      <ContextMenu.Portal>
        <ContextMenu.Content className={contentClass}>
          <ColumnMenuItems
            Item={ContextMenu.Item}
            Group={ContextMenu.Group}
            Separator={ContextMenu.Separator}
            Label={ContextMenu.Label}
            column={column}
            onAction={onAction}
          />
        </ContextMenu.Content>
      </ContextMenu.Portal>
    </ContextMenu.Root>
  );
};
