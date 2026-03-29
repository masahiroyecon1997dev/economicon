import { useTranslation } from "react-i18next";
import { InputText } from "../../atoms/Input/InputText";
import { FormField } from "./FormField";

type RandomSeedFieldProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  error?: string;
};

export const RandomSeedField = ({
  id = "random-seed",
  value,
  onChange,
  onBlur,
  disabled,
  error,
}: RandomSeedFieldProps) => {
  const { t } = useTranslation();

  return (
    <FormField label={t("Common.RandomSeed")} htmlFor={id} error={error}>
      <InputText
        id={id}
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        placeholder={t("Common.RandomSeedPlaceholder")}
        min={0}
        max={100_000_000}
        step={1}
        disabled={disabled}
        error={error}
      />
    </FormField>
  );
};
