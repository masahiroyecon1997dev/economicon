import { ConfidenceIntervalForm } from "@/components/organisms/Form/ConfidenceIntervalForm";
import { PageLayout } from "@/components/templates/PageLayout";
import { useCurrentPageStore } from "@/stores/currentView";

type ConfidenceIntervalViewProps = {
  className?: string;
};

export const ConfidenceIntervalView = ({
  className: _className,
}: ConfidenceIntervalViewProps) => {
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);

  const handleCancel = () => {
    setCurrentView("DataPreview");
  };

  return (
    <PageLayout>
      <ConfidenceIntervalForm onCancel={handleCancel} />
    </PageLayout>
  );
};
