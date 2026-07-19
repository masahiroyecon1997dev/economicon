import type { TobitParams } from "@/api/model";

/** Tobit フォーム内部の analysis 状態（UI 専用。API 送信前に変換が必要） */
export type TobitFormAnalysis = {
  method: "tobit";
  leftCensoringEnabled: boolean;
  leftCensoringLimit: number;
  rightCensoringEnabled: boolean;
  rightCensoringLimit: number;
};

/**
 * Tobit フォームのデフォルト analysis 状態を返す。
 * - 左打ち切りはデフォルトで有効（値: 0）
 * - 右打ち切りはデフォルトで無効
 */
export const buildTobitDefaultAnalysis = (): TobitFormAnalysis => ({
  method: "tobit",
  leftCensoringEnabled: true,
  leftCensoringLimit: 0,
  rightCensoringEnabled: false,
  rightCensoringLimit: 0,
});

/**
 * Tobit フォームの analysis 状態を API 送信用 TobitParams に変換する。
 * - `*CensoringEnabled: false` のときは対応する limit を `null` にする
 */
export const buildTobitRequestParams = (
  analysis: TobitFormAnalysis,
): TobitParams => ({
  method: "tobit",
  leftCensoringLimit: analysis.leftCensoringEnabled
    ? analysis.leftCensoringLimit
    : null,
  rightCensoringLimit: analysis.rightCensoringEnabled
    ? analysis.rightCensoringLimit
    : null,
});
