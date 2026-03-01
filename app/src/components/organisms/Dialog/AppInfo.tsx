import { useTranslation } from "react-i18next";
import { Dialog } from "../../molecules/Dialog/Dialog";

type CalculateProps = {
  isCalculateDialog: boolean;
  close: () => void;
};

export const Calculate = ({ isCalculateDialog, close }: CalculateProps) => {
  const { t } = useTranslation();

  const calculate = () => {};

  return (
    <Dialog
      isOpenDialog={isCalculateDialog}
      modalTitle={t("AppInfo.Title")}
      submitButtonName={t("CalculateDialog.Execute")}
      submit={calculate}
      close={close}
      modalSize="max-w-2xl"
    >
      <div className="grid grid-cols-3 gap-4 leading-6">
        <p>
          Icons by
          <a
            href="https://fontawesome.com/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Font Awesome
          </a>
          , licensed under
          <a
            href="https://creativecommons.org/licenses/by/4.0/"
            target="_blank"
            rel="noopener noreferrer"
          >
            CC BY 4.0
          </a>
          .
        </p>
      </div>
    </Dialog>
  );
};
