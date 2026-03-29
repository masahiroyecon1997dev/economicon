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
