import { CommonRegressionForm } from "@/components/organisms/Form/CommonRegressionForm";

type LinearRegressionFormProps = {
  onCancel: () => void;
};

export const LinearRegressionForm = ({
  onCancel,
}: LinearRegressionFormProps) => {
  return (
    <CommonRegressionForm
      onCancel={onCancel}
      method="ols"
      titleKey="LinearRegressionForm.Title"
      descriptionKey="LinearRegressionForm.Description"
    />
  );
};
