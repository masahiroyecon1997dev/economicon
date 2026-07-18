import { CommonRegressionForm } from "@/components/organisms/Form/CommonRegressionForm";

type WLSRegressionFormProps = {
  onCancel: () => void;
};

export const WLSRegressionForm = ({ onCancel }: WLSRegressionFormProps) => {
  return (
    <CommonRegressionForm
      onCancel={onCancel}
      method="wls"
      titleKey="WLSRegressionForm.Title"
      descriptionKey="WLSRegressionForm.Description"
    />
  );
};
