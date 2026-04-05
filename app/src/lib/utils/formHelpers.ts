/**
 * @tanstack/react-form の Zod バリデーションエラーオブジェクトから
 * 表示用文字列を抽出するユーティリティ。
 *
 * zodValidator が返すエラーは `{ message: string }` 形式のオブジェクト、
 * 直接バリデータが返す場合は文字列になる。どちらにも対応する。
 */
export const extractFieldError = (
  errors: unknown[],
  mapFn?: (raw: string) => string,
): string | undefined => {
  const e = errors[0];
  if (!e) return undefined;
  const raw = (e as { message?: string })?.message ?? String(e);
  return mapFn ? mapFn(raw) : raw;
};

/**
 * i18n キー固定のエラーマッパーを生成するファクトリ。
 * コンポーネント内で `const tErr = createFieldError(t)` として使う。
 *
 * @example
 *   const tErr = createFieldError(t);
 *   tErr(field.state.meta.errors, "ValidationMessages.NewColumnNameRequired")
 */
export const createFieldError =
  (t: (key: string) => string) =>
  (errors: unknown[], i18nKey: string): string | undefined =>
    extractFieldError(errors, () => t(i18nKey));
