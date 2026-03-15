import { useTranslation } from "react-i18next";
import { useConfirmDialogStore } from "../../../stores/confirmDialog";
import { BaseDialog } from "./BaseDialog";

export const ConfirmDialog = () => {
  const { t } = useTranslation();
  const { isOpen, title, message, confirmDialog, cancelDialog } =
    useConfirmDialogStore();

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={(open) => !open && cancelDialog()}
      title={title}
      footerVariant="confirm"
      submitLabel={t("Common.OK")}
      onSubmit={confirmDialog}
    >
      <p className="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap">
        {message}
      </p>
    </BaseDialog>
  );
};
