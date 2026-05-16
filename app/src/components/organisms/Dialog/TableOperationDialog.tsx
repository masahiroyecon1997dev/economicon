/**
 * テーブル操作ダイアログ
 *
 * TableNavItem からの操作イベントを受け取り、
 * 対応するフォームコンポーネントを BaseDialog で表示する。
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { DeleteTableForm } from "@/components/organisms/Dialog/TableOperationForms/DeleteTableForm";
import { DuplicateTableForm } from "@/components/organisms/Dialog/TableOperationForms/DuplicateTableForm";
import { RenameTableForm } from "@/components/organisms/Dialog/TableOperationForms/RenameTableForm";

export type TableOperation = "rename" | "duplicate" | "delete";

type TableOperationDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  operation: TableOperation | null;
  tableName: string;
};

const getDialogTitle = (
  operation: TableOperation | null,
  t: (key: string) => string,
): string => {
  switch (operation) {
    case "rename":
      return t("RenameTableForm.Title");
    case "duplicate":
      return t("DuplicateTableForm.Title");
    case "delete":
      return t("DeleteTableForm.Title");
    default:
      return "";
  }
};

const getSubmitLabel = (
  operation: TableOperation | null,
  t: (key: string) => string,
): string => {
  switch (operation) {
    case "rename":
      return t("RenameTableForm.Submit");
    case "duplicate":
      return t("DuplicateTableForm.Submit");
    case "delete":
      return t("Common.Delete");
    default:
      return t("Common.OK");
  }
};

export const TableOperationDialog = ({
  open,
  onOpenChange,
  operation,
  tableName,
}: TableOperationDialogProps) => {
  const { t } = useTranslation();
  const [isFormSubmitting, setIsFormSubmitting] = useState(false);

  if (!operation) return null;

  const handleSuccess = () => {
    onOpenChange(false);
  };

  const FORM_ID = "table-op-form";

  const renderForm = () => {
    switch (operation) {
      case "rename":
        return (
          <RenameTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            formId={FORM_ID}
            onIsSubmittingChange={setIsFormSubmitting}
          />
        );
      case "duplicate":
        return (
          <DuplicateTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            formId={FORM_ID}
            onIsSubmittingChange={setIsFormSubmitting}
          />
        );
      case "delete":
        return (
          <DeleteTableForm
            tableName={tableName}
            onSuccess={handleSuccess}
            formId={FORM_ID}
            onIsSubmittingChange={setIsFormSubmitting}
          />
        );
      default:
        return null;
    }
  };

  return (
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={getDialogTitle(operation, t)}
      subtitle={tableName}
      footerVariant="confirm"
      submitLabel={getSubmitLabel(operation, t)}
      submitFormId={FORM_ID}
      isSubmitting={isFormSubmitting}
      submitVariant={operation === "delete" ? "danger" : "primary"}
    >
      {renderForm()}
    </BaseDialog>
  );
};
