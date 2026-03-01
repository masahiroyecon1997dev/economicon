/**
 * 列�EチE��ーのコンチE��ストメニューコンポ�EネンチE *
 * - MoreVertical アイコン�E�Eroup-hover で表示�E�を起点に Radix DropdownMenu を開ぁE * - sort_asc / sort_desc は直接 API コール�E�ダイアログなし！E * - そ�E他�E操作�E親コンポ�Eネントへ operation イベントを伝達
 */
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import {
  ArrowDownAZ,
  ArrowUpAZ,
  CopyPlus,
  FileClock,
  FlipHorizontal,
  MoreVertical,
  Sigma,
  Tags,
  Trash2,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import type { ColumnType } from "../../../types/commonTypes";

export type ColumnOperation =
  | "sort_asc"
  | "sort_desc"
  | "rename"
  | "duplicate"
  | "cast"
  | "transform"
  | "addDummy"
  | "addLagLead"
  | "delete";

type ColumnContextMenuProps = {
  column: ColumnType;
  onAction: (operation: ColumnOperation) => void;
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
);

export const ColumnContextMenu = ({
  column,
  onAction,
}: ColumnContextMenuProps) => {
  const { t } = useTranslation();

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className={cn(
            "ml-1 rounded p-0.5 opacity-0 group-hover:opacity-100 transition-opacity",
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
          className={cn(
            "z-50 min-w-50 rounded-md bg-white dark:bg-gray-800 shadow-lg",
            "border border-gray-200 dark:border-gray-700",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=open]:fade-in-0 data-[state=closed]:fade-out-0",
            "data-[state=open]:zoom-in-95 data-[state=closed]:zoom-out-95",
          )}
        >
          {/* ソーチE*/}
          <DropdownMenu.Group className="p-1">
            <DropdownMenu.Label className="px-2 py-1 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
              {column.name}
            </DropdownMenu.Label>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("sort_asc")}
            >
              <ArrowUpAZ className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.SortAsc")}
            </DropdownMenu.Item>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("sort_desc")}
            >
              <ArrowDownAZ className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.SortDesc")}
            </DropdownMenu.Item>
          </DropdownMenu.Group>

          <DropdownMenu.Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />

          {/* 列編雁E*/}
          <DropdownMenu.Group className="p-1">
            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("rename")}
            >
              <FlipHorizontal className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.Rename")}
            </DropdownMenu.Item>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("duplicate")}
            >
              <CopyPlus className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.Duplicate")}
            </DropdownMenu.Item>
          </DropdownMenu.Group>

          <DropdownMenu.Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />

          {/* 列追加系 */}
          <DropdownMenu.Group className="p-1">
            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("cast")}
            >
              <Sigma className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.Cast")}
            </DropdownMenu.Item>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("transform")}
            >
              <Sigma className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.Transform")}
            </DropdownMenu.Item>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("addDummy")}
            >
              <Tags className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.AddDummy")}
            </DropdownMenu.Item>

            <DropdownMenu.Item
              className={menuItemClass}
              onSelect={() => onAction("addLagLead")}
            >
              <FileClock className="h-4 w-4 text-gray-500 shrink-0" />
              {t("ColumnMenu.AddLagLead")}
            </DropdownMenu.Item>
          </DropdownMenu.Group>

          <DropdownMenu.Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />

          {/* 削除 */}
          <DropdownMenu.Group className="p-1">
            <DropdownMenu.Item
              className={destructiveItemClass}
              onSelect={() => onAction("delete")}
            >
              <Trash2 className="h-4 w-4 shrink-0" />
              {t("ColumnMenu.Delete")}
            </DropdownMenu.Item>
          </DropdownMenu.Group>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
};
