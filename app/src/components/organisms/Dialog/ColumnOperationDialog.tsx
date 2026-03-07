/**
 * 列操作ダイアログ
 *
 * ColumnContextMenu からの操作イベントを受け取り、
 * 対応するフォームコンポーネントを BaseDialog で表示する。
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ColumnType } from "../../../types/commonTypes";
import { BaseDialog } from "../../molecules/Dialog/BaseDialog";
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

/** ダイアログの送信ボタンラベル */
const getSubmitLabel = (
  operation: ColumnOperation | null,
  t: (key: string) => string,
): string => {
  switch (operation) {
    case "rename":
      return t("RenameColumnForm.Submit");
    case "delete":
      return t("DeleteColumnForm.Submit");
    case "duplicate":
      return t("DuplicateColumnForm.Submit");
    case "cast":
      return t("CastColumnForm.Submit");
    case "transform":
      return t("TransformColumnForm.Submit");
    case "addDummy":
      return t("AddDummyColumnForm.Submit");
    case "addLagLead":
      return t("AddLagLeadColumnForm.Submit");
    case "addSimulation":
      return t("AddSimulationColumnForm.Submit");
    default:
      return t("Common.OK");
  }
};

/** ダイアログの幅 */
const getMaxWidth = (operation: ColumnOperation | null): "md" | "lg" => {
  switch (operation) {
    case "cast":
    case "transform":
    case "addDummy":
    case "addLagLead":
    case "addSimulation":
      return "lg";
    default:
      return "md";
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
  const [isFormSubmitting, setIsFormSubmitting] = useState(false);

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

  const FORM_ID = "col-op-form";

  const formProps = {
    tableName,
    column,
    formId: FORM_ID,
    onIsSubmittingChange: setIsFormSubmitting,
    onSuccess: handleSuccess,
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
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={getDialogTitle(operation, t)}
      subtitle={`${column.name} (${column.type})`}
      maxWidth={getMaxWidth(operation)}
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
