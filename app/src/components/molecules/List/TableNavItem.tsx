import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { Copy, MoreVertical, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";
import type { TableOperation } from "../../organisms/Dialog/TableOperationDialog";
import { TableOperationDialog } from "../../organisms/Dialog/TableOperationDialog";

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
      <div
        className={cn(
          // ベーススタイル
          "group flex items-center gap-1 rounded-md px-3 py-2 transition-colors",
          // アクティブ / 非アクティブ
          isActive
            ? "bg-white/20 font-medium text-white hover:bg-white/25"
            : "font-normal text-white/70 hover:bg-white/10 hover:text-white",
        )}
      >
        {/* テーブル名（省略表示）: span のみクリック可能にして DropdownMenu との干渉を防ぐ */}
        <span
          className="flex-1 min-w-0 block truncate text-sm cursor-pointer"
          title={tableName}
          onClick={() => onClick(tableName)}
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
              aria-label={t("AreaLabels.TableMenu")}
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
              {/* リネーム */}
              <DropdownMenu.Item
                className={cn(
                  "flex items-center gap-2 rounded-t-md px-3 py-2 text-sm",
                  "text-gray-700 dark:text-gray-200 outline-none cursor-pointer transition-colors",
                  "data-highlighted:bg-gray-100 dark:data-highlighted:bg-gray-700",
                )}
                onSelect={() => openDialog("rename")}
              >
                <Pencil className="w-4 h-4 shrink-0" />
                <span>{t("LeftSideMenu.MenuRenameTable")}</span>
              </DropdownMenu.Item>

              {/* 複製 */}
              <DropdownMenu.Item
                className={cn(
                  "flex items-center gap-2 px-3 py-2 text-sm",
                  "text-gray-700 dark:text-gray-200 outline-none cursor-pointer transition-colors",
                  "data-highlighted:bg-gray-100 dark:data-highlighted:bg-gray-700",
                )}
                onSelect={() => openDialog("duplicate")}
              >
                <Copy className="w-4 h-4 shrink-0" />
                <span>{t("LeftSideMenu.MenuDuplicateTable")}</span>
              </DropdownMenu.Item>

              <DropdownMenu.Separator className="h-px bg-gray-100 dark:bg-gray-700 mx-1" />

              {/* 削除 */}
              <DropdownMenu.Item
                className={cn(
                  "flex items-center gap-2 rounded-b-md px-3 py-2 text-sm",
                  "text-red-600 dark:text-red-400 outline-none cursor-pointer transition-colors",
                  "data-highlighted:bg-red-50 dark:data-highlighted:bg-red-950/50",
                )}
                onSelect={() => openDialog("delete")}
              >
                <Trash2 className="w-4 h-4 shrink-0" />
                <span>{t("LeftSideMenu.MenuDeleteTable")}</span>
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>

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
