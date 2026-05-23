import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { useConfirmDialogStore } from "@/stores/confirmDialog";
import { useTranslation } from "react-i18next";

export const ConfirmDialog = () => {
  const { t } = useTranslation();
  const { isOpen, title, message, submitVariant, confirmDialog, cancelDialog } =
    useConfirmDialogStore();

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={(open) => !open && cancelDialog()}
      title={title}
      footerVariant="confirm"
      submitLabel={t("Common.OK")}
      submitVariant={submitVariant}
      onSubmit={confirmDialog}
    >
      <p className="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap">
        {message}
      </p>
    </BaseDialog>
  );
};
