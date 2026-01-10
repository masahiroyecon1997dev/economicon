// src/components/atoms/button/button.tsx
import { type ComponentPropsWithoutRef } from "react";
import { cn } from "../../../functions/utils";

// スタイル定義を外に出して整理
const variants = {
  // 元の submit
  primary: cn(
    "bg-brand-accent text-white shadow-sm hover:bg-brand-accent/90",
    "focus-visible:outline focus-visible:outline-offset-2 focus-visible:outline-brand-accent"
  ),
  // 元の cancel
  outline: cn(
    "bg-white text-main border border-border-color hover:bg-gray-50",
    "dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600"
  ),
  // 他にも必要になったらここに追加しやすい（ghost など）
};

type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: keyof typeof variants;
};

export const Button = ({
  children,
  variant = "primary",
  className,
  type = "button", // デフォルトをbuttonにしておくと誤送信を防げる
  ...props // onClick や disabled などをまとめて受け取る
}: ButtonProps) => {
  return (
    <button
      type={type}
      className={cn(
        "rounded-md px-6 py-2.5 text-sm font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};
