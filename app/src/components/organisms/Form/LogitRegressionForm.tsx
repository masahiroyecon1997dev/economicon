import { CommonRegressionForm } from "@/components/organisms/Form/CommonRegressionForm";

type LogitRegressionFormProps = {
  onCancel: () => void;
};

export const LogitRegressionForm = ({ onCancel }: LogitRegressionFormProps) => {
  return (
    <CommonRegressionForm
      onCancel={onCancel}
      method="logit"
      titleKey="LogitRegressionForm.Title"
      descriptionKey="LogitRegressionForm.Description"
    />
  );
};
