import type { ErrorResponse } from "../../api/model/errorResponse";

/**
 * レスポンスオブジェクト（code !== "OK"）からエラーメッセージを取得する。
 * サーバー側が多言語化済みのmessageフィールドを持つためそのまま使用できる。
 */
export const getResponseErrorMessage = (
  response: unknown,
  fallback: string,
): string => {
  const r = response as Partial<ErrorResponse>;
  return r.message ?? fallback;
};

/**
 * catch ブロックの error オブジェクトからエラーメッセージを取得する。
 *
 * Tauri の invoke は HTTP エラーレスポンスをそのまま文字列として throw するため、
 * JSON.parse を試みてサーバー側のメッセージを取り出す。
 */
export const extractApiErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  // Tauri invoke が throw するエラーは文字列の場合がある
  const raw =
    typeof error === "string"
      ? error
      : error instanceof Error
        ? error.message
        : null;

  if (raw) {
    try {
      const body = JSON.parse(raw) as Partial<ErrorResponse>;
      if (body.message) return body.message;
    } catch {
      // JSON でなければ生のメッセージをそのまま使う
    }
    return raw;
  }

  return fallback;
};
