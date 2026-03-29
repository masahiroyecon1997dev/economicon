import * as ContextMenu from "@radix-ui/react-context-menu";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Copy, MoreVertical, Pencil, Trash2 } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import type { TableOperation } from "../../organisms/Dialog/TableOperationDialog";
import { TableOperationDialog } from "../../organisms/Dialog/TableOperationDialog";

// ---------------------------------------------------------------------------
// 共通スロット型: ContextMenu / DropdownMenu 両方と互換
// ---------------------------------------------------------------------------
type MenuSlots = {
  Item: ComponentType<{
    className?: string;
    onSelect?: (event: Event) => void;
    children?: ReactNode;
  }>;
  Separator: ComponentType<{ className?: string }>;
};

type TableNavMenuItemsProps = MenuSlots & {
  onAction: (op: TableOperation) => void;
};

const itemClass = cn(
  "flex items-center gap-2 px-3 py-2 text-sm outline-none cursor-pointer transition-colors",
  "text-gray-700 dark:text-gray-200",
  "data-highlighted:bg-gray-100 dark:data-highlighted:bg-gray-700",
);
const destructiveItemClass = cn(
  "flex items-center gap-2 px-3 py-2 text-sm outline-none cursor-pointer transition-colors",
  "text-red-600 dark:text-red-400",
  "data-highlighted:bg-red-50 dark:data-highlighted:bg-red-950/50",
);

const TableNavMenuItems = ({
  Item,
  Separator,
  onAction,
}: TableNavMenuItemsProps) => {
  const { t } = useTranslation();
  return (
    <>
      <Item className={itemClass} onSelect={() => onAction("rename")}>
        <Pencil className="w-4 h-4 shrink-0" />
        <span>{t("LeftSideMenu.MenuRenameData")}</span>
      </Item>
      <Item className={itemClass} onSelect={() => onAction("duplicate")}>
        <Copy className="w-4 h-4 shrink-0" />
        <span>{t("LeftSideMenu.MenuDuplicateData")}</span>
      </Item>
      <Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />
      <Item
        className={destructiveItemClass}
        onSelect={() => onAction("delete")}
      >
        <Trash2 className="w-4 h-4 shrink-0" />
        <span>{t("LeftSideMenu.MenuDeleteData")}</span>
      </Item>
    </>
  );
};

type TableNavItemProps = {
  tableName: string;
  isActive: boolean;
  onClick: (tableName: string) => void;
};

export const TableNavItem = ({
  tableName,
  isActive,
  onClick,
}: TableNavItemProps) => {
  const { t } = useTranslation();
  const [dialogOperation, setDialogOperation] = useState<TableOperation | null>(
    null,
  );
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const openDialog = (op: TableOperation) => {
    setDialogOperation(op);
    setIsDialogOpen(true);
  };

  return (
    <>
      <ContextMenu.Root>
        <ContextMenu.Trigger asChild>
          <div
            className={cn(
              // ベーススタイル
              "group flex items-center gap-1 rounded-md px-3 py-2 transition-colors cursor-pointer",
              // アクティブ / 非アクティブ
              isActive
                ? "bg-white/20 font-medium text-white hover:bg-white/25"
                : "font-normal text-white/70 hover:bg-white/10 hover:text-white",
            )}
            onClick={() => onClick(tableName)}
          >
            <span
              className="flex-1 min-w-0 block truncate text-sm"
              title={tableName}
            >
              {tableName}
            </span>

            {/* 縦三点リーダー: ホバー時 or メニュー開放時のみ表示 */}
            <DropdownMenu.Root>
              <DropdownMenu.Trigger asChild>
                <button
                  type="button"
                  className={cn(
                    "shrink-0 rounded p-0.5 transition-opacity",
                    "opacity-0 group-hover:opacity-100 data-[state=open]:opacity-100",
                    "hover:bg-white/20 data-[state=open]:bg-white/20",
                    "focus:outline-none focus-visible:ring-1 focus-visible:ring-white/50",
                  )}
                  aria-label={t("AreaLabels.DataMenu")}
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical size={14} />
                </button>
              </DropdownMenu.Trigger>
              <DropdownMenu.Portal>
                <DropdownMenu.Content
                  side="bottom"
                  align="start"
                  sideOffset={4}
                  className={cn(
                    "z-50 min-w-44 rounded-md bg-white dark:bg-gray-800 shadow-lg",
                    "border border-gray-200 dark:border-gray-700",
                    "data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out",
                  )}
                >
                  <TableNavMenuItems
                    Item={DropdownMenu.Item}
                    Separator={DropdownMenu.Separator}
                    onAction={openDialog}
                  />
                </DropdownMenu.Content>
              </DropdownMenu.Portal>
            </DropdownMenu.Root>
          </div>
        </ContextMenu.Trigger>

        <ContextMenu.Portal>
          <ContextMenu.Content
            className={cn(
              "z-50 min-w-44 rounded-md bg-white dark:bg-gray-800 shadow-lg",
              "border border-gray-200 dark:border-gray-700",
              "data-[state=open]:animate-fade-in data-[state=closed]:animate-fade-out",
            )}
          >
            <TableNavMenuItems
              Item={ContextMenu.Item}
              Separator={ContextMenu.Separator}
              onAction={openDialog}
            />
          </ContextMenu.Content>
        </ContextMenu.Portal>
      </ContextMenu.Root>

      {/* テーブル操作ダイアログ */}
      <TableOperationDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        operation={dialogOperation}
        tableName={tableName}
      />
    </>
  );
};
