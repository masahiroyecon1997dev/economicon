import { CommonRegressionForm } from "@/components/organisms/Form/CommonRegressionForm";

type ProbitRegressionFormProps = {
  onCancel: () => void;
};

export const ProbitRegressionForm = ({
  onCancel,
}: ProbitRegressionFormProps) => {
  return (
    <CommonRegressionForm
      onCancel={onCancel}
      method="probit"
      titleKey="ProbitRegressionForm.Title"
      descriptionKey="ProbitRegressionForm.Description"
    />
  );
};
