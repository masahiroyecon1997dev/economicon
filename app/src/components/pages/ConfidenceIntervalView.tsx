import { ConfidenceIntervalForm } from "@/components/organisms/Form/ConfidenceIntervalForm";
import { PageLayout } from "@/components/templates/PageLayout";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { useTranslation } from "react-i18next";

type ConfidenceIntervalViewProps = {
  className?: string;
};

export const ConfidenceIntervalView = ({
  className: _className,
}: ConfidenceIntervalViewProps) => {
  const { t } = useTranslation();
  const closeActiveWorkTab = useWorkspaceTabsStore((s) => s.closeActiveWorkTab);

  return (
    <PageLayout
      title={t("ConfidenceIntervalView.Title")}
      description={t("ConfidenceIntervalView.Description")}
    >
      <ConfidenceIntervalForm onCancel={closeActiveWorkTab} />
    </PageLayout>
  );
};
