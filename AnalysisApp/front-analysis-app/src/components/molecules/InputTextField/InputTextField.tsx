import React, { ChangeEvent } from "react";
import { useTranslation } from "react-i18next";

import { InputText } from "../../atoms/InputText/InputText";

type InputFieldTextMiddleProps = {
  label: string;
  value: string;
  change: (event: ChangeEvent<HTMLInputElement>) => void;
  error: string;
};

export function InputTextField({
  label,
  value,
  change,
  error,
}: InputFieldTextMiddleProps) {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-3 gap-4 leading-6">
      <div className="p-4 rounded-lg text-right text-lg content-center">
        {label}
      </div>
      <div className="p-4 rounded-lg col-span-2">
        <InputText
          value={value}
          change={(event) => change(event)}
          error={error}
        />
        {error !== "" ? (
          <p className="text-red-500 text-xs mt-1">{t(error)}</p>
        ) : null}
      </div>
    </div>
  );
}
