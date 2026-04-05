import { useEffect } from "react";

/**
 * フォームの isSubmitting 状態が変化したときに onIsSubmittingChange を呼び出すフック。
 *
 * 各フォームで繰り返されていた
 * ```ts
 * useEffect(() => { onIsSubmittingChange(isSubmitting); }, [isSubmitting, onIsSubmittingChange]);
 * ```
 * を集約する。
 */
export const useFormSubmitting = (
  isSubmitting: boolean,
  onIsSubmittingChange: (isSubmitting: boolean) => void,
): void => {
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);
};
