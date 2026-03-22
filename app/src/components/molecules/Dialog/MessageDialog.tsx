import { useTranslation } from "react-i18next";
import { useMessageDialogStore } from "../../../stores/messageDialog";
import { BaseDialog } from "./BaseDialog";

export const MessageDialog = () => {
  const { t } = useTranslation();
  const { isOpen, title, message, closeMessageDialog } =
    useMessageDialogStore();

  return (
    <BaseDialog
      open={isOpen}
      onOpenChange={(open) => !open && closeMessageDialog()}
      title={title}
      footerVariant="ok"
      submitLabel={t("Common.OK")}
      onSubmit={closeMessageDialog}
    >
      <p className="text-sm text-gray-900 dark:text-gray-200 whitespace-pre-wrap">
        {message}
      </p>
    </BaseDialog>
  );
};
