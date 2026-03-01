import { forwardRef, type ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { cn } from "../../../lib/utils/helpers";

// 1. React標準のinput属性を継承しつつ、既存の独自プロパティ(change等)も許容する
type InputTextProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  "onChange"
> & {
  // 既存の change プロパティ（互換性のために残す）
  change?: (_event: ChangeEvent<HTMLInputElement>) => void;
  // RHFや標準が使うプロパティ
  onChange?: (_event: ChangeEvent<HTMLInputElement>) => void;
  error?: string;
};

export const InputText = forwardRef<HTMLInputElement, InputTextProps>(
  (
    {
      value,
      change, // 既存の props
      onChange, // registerから渡される props
      error = "",
      placeholder,
      type = "text",
      step,
      id,
      name,
      className,
      disabled = false,
      ...props // その他の属性（onBlurなど）をまとめる
    },
    ref,
  ) => {
    const { t } = useTranslation();

    // 2. 既存の change または標準の onChange どちらが来ても動くように統合
    const handleOnChange = (event: ChangeEvent<HTMLInputElement>) => {
      if (change) change(event);
      if (onChange) onChange(event);
    };

    return (
      <div className="w-full">
        <input
          ref={ref} // 3. これにより RHF がこの input を認識できる
          type={type}
          step={step}
          id={id}
          name={name}
          className={cn(
            "w-full px-2.5 py-1.5 text-sm font-normal text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700 border rounded-md shadow-sm",
            "placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors duration-200",
            error
              ? "border-red-500 focus:ring-red-500 focus:border-red-500 dark:border-red-500/60"
              : "border-gray-300 dark:border-gray-600 focus:ring-gray-700 dark:focus:ring-gray-500 focus:border-gray-700 dark:focus:border-gray-500 hover:border-gray-400 dark:hover:border-gray-500",
            className,
          )}
          value={value}
          onChange={handleOnChange}
          placeholder={placeholder}
          disabled={disabled}
          {...props} // 4. RHFから渡される可能性があるその他の属性を適用
        />
        <div className="h-4 mt-0.5">
          {error && (
            <p className="text-xs text-red-600">
              {/* バリデーションエラーがそのまま翻訳キーになるよう調整 */}
              {t(error)}
            </p>
          )}
        </div>
      </div>
    );
  },
);

InputText.displayName = "InputText";
