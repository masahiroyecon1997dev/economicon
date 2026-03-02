/**
 * 列操作ダイアログ
 *
 * ColumnContextMenu からの操作イベントを受け取り、
 * 対応するフォームコンポーネントを Radix Dialog で表示する。
 */
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { ColumnType } from "../../../types/commonTypes";
import type { ColumnOperation } from "../../organisms/Table/ColumnContextMenu";
import { AddDummyColumnForm } from "./ColumnOperationForms/AddDummyColumnForm";
import { AddLagLeadColumnForm } from "./ColumnOperationForms/AddLagLeadColumnForm";
import { AddSimulationColumnForm } from "./ColumnOperationForms/AddSimulationColumnForm";
import { CastColumnForm } from "./ColumnOperationForms/CastColumnForm";
import { DeleteColumnForm } from "./ColumnOperationForms/DeleteColumnForm";
import { DuplicateColumnForm } from "./ColumnOperationForms/DuplicateColumnForm";
import { RenameColumnForm } from "./ColumnOperationForms/RenameColumnForm";
import { TransformColumnForm } from "./ColumnOperationForms/TransformColumnForm";

type ColumnOperationDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  operation: ColumnOperation | null;
  tableName: string;
  column: ColumnType | null;
  onSuccess: (updatedColumnList: ColumnType[]) => void;
};

const getDialogTitle = (
  operation: ColumnOperation | null,
  t: (key: string) => string,
): string => {
  switch (operation) {
    case "rename":
      return t("RenameColumnForm.Title");
    case "delete":
      return t("DeleteColumnForm.Title");
    case "duplicate":
      return t("DuplicateColumnForm.Title");
    case "cast":
      return t("CastColumnForm.Title");
    case "transform":
      return t("TransformColumnForm.Title");
    case "addDummy":
      return t("AddDummyColumnForm.Title");
    case "addLagLead":
      return t("AddLagLeadColumnForm.Title");
    case "addSimulation":
      return t("AddSimulationColumnForm.Title");
    default:
      return "";
  }
};

/** ダイアログの幅クラス */
const getDialogWidth = (operation: ColumnOperation | null): string => {
  switch (operation) {
    case "cast":
    case "transform":
    case "addDummy":
    case "addLagLead":
    case "addSimulation":
      return "max-w-lg";
    default:
      return "max-w-md";
  }
};

export const ColumnOperationDialog = ({
  open,
  onOpenChange,
  operation,
  tableName,
  column,
  onSuccess,
}: ColumnOperationDialogProps) => {
  const { t } = useTranslation();

  if (!column || !operation) {
    return null;
  }

  // sort は直接 API コールのためダイアログは不要
  if (operation === "sort_asc" || operation === "sort_desc") {
    return null;
  }

  const handleSuccess = (updatedColumnList: ColumnType[]) => {
    onSuccess(updatedColumnList);
    onOpenChange(false);
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  const formProps = {
    tableName,
    column,
    onSuccess: handleSuccess,
    onClose: handleClose,
  };

  const renderForm = () => {
    switch (operation) {
      case "rename":
        return <RenameColumnForm {...formProps} />;
      case "delete":
        return <DeleteColumnForm {...formProps} />;
      case "duplicate":
        return <DuplicateColumnForm {...formProps} />;
      case "cast":
        return <CastColumnForm {...formProps} />;
      case "transform":
        return <TransformColumnForm {...formProps} />;
      case "addDummy":
        return <AddDummyColumnForm {...formProps} />;
      case "addLagLead":
        return <AddLagLeadColumnForm {...formProps} />;
      case "addSimulation":
        return <AddSimulationColumnForm {...formProps} />;
      default:
        return null;
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-gray-900/40" />
        <Dialog.Content
          className={`fixed left-1/2 top-[48%] z-50 w-full ${getDialogWidth(operation)} -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white dark:bg-gray-900 shadow-xl overflow-hidden`}
        >
          {/* ヘッダー */}
          <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-5 py-4">
            <div>
              <Dialog.Title className="text-base font-semibold text-gray-900 dark:text-gray-100">
                {getDialogTitle(operation, t)}
              </Dialog.Title>
              <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 font-mono">
                {column.name}
                <span className="ml-2 text-gray-400 dark:text-gray-500">
                  ({column.type})
                </span>
              </p>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="rounded-lg p-1.5 text-gray-400 dark:text-gray-500 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
                aria-label={t("Common.Close")}
              >
                <X className="h-4 w-4" />
              </button>
            </Dialog.Close>
          </div>

          {/* フォーム本体 */}
          <Dialog.Description asChild>
            <div className="px-5 py-4 dark:text-gray-200">{renderForm()}</div>
          </Dialog.Description>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
