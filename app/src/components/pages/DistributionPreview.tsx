import { useTranslation } from "react-i18next";

export const DistributionPreview = () => {
  const { t } = useTranslation();

  return (
    <div
      className="flex h-full items-center justify-center text-gray-400"
      data-testid="distribution-preview-placeholder"
    >
      {t("HeaderMenu.DistributionPreview")}
    </div>
  );
};
