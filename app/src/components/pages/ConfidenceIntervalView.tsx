import { ExplainerButton } from "@/components/molecules/Dialog/ExplainerButton";
import { ConfidenceIntervalForm } from "@/components/organisms/Form/ConfidenceIntervalForm";
import { PageLayout } from "@/components/templates/PageLayout";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";
import { HelpCircle } from "lucide-react";
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
      titleAction={
        <ExplainerButton
          explainerKey="confidence_interval"
          className="rounded-full p-0.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-brand-accent dark:hover:bg-gray-800 dark:hover:text-brand-accent"
          aria-label={t("ConfidenceIntervalView.ExplainerButtonLabel")}
          data-testid="confidence-interval-explainer-btn"
        >
          <HelpCircle size={16} aria-hidden="true" />
        </ExplainerButton>
      }
    >
      <ConfidenceIntervalForm onCancel={closeActiveWorkTab} />
    </PageLayout>
  );
};
