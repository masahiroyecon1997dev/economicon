import { ConfidenceIntervalForm } from "@/components/organisms/Form/ConfidenceIntervalForm";
import { PageLayout } from "@/components/templates/PageLayout";
import { useWorkspaceTabsStore } from "@/stores/workspaceTabs";

type ConfidenceIntervalViewProps = {
  className?: string;
};

export const ConfidenceIntervalView = ({
  className: _className,
}: ConfidenceIntervalViewProps) => {
  const closeActiveWorkTab = useWorkspaceTabsStore((s) => s.closeActiveWorkTab);

  return (
    <PageLayout>
      <ConfidenceIntervalForm onCancel={closeActiveWorkTab} />
    </PageLayout>
  );
};
