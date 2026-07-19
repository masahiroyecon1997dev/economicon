import { CommonRegressionForm } from "@/components/organisms/Form/CommonRegressionForm";

type TobitRegressionFormProps = {
  onCancel: () => void;
};

export const TobitRegressionForm = ({ onCancel }: TobitRegressionFormProps) => {
  return (
    <CommonRegressionForm
      onCancel={onCancel}
      method="tobit"
      titleKey="TobitRegressionForm.Title"
      descriptionKey="TobitRegressionForm.Description"
    />
  );
};
