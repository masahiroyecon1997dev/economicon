/**
 * CommonRegressionForm — Tobit 固有ロジックのユニットテスト
 *
 * テスト対象:
 * - buildTobitDefaultAnalysis: フォームのデフォルト初期値が正しいこと
 * - buildTobitRequestParams:   フォーム状態 → API パラメータへの変換ロジック
 *   （leftCensoringEnabled / rightCensoringEnabled が false のとき null に変換されること）
 */
import { describe, expect, it } from "vitest";
import {
  buildTobitDefaultAnalysis,
  buildTobitRequestParams,
} from "./CommonRegressionForm.utils";

// ---------------------------------------------------------------------------
// buildTobitDefaultAnalysis
// ---------------------------------------------------------------------------
describe("buildTobitDefaultAnalysis", () => {
  it("左打ち切りがデフォルトで有効・値 0 になること", () => {
    const result = buildTobitDefaultAnalysis();
    expect(result.leftCensoringEnabled).toBe(true);
    expect(result.leftCensoringLimit).toBe(0);
  });

  it("右打ち切りがデフォルトで無効になること", () => {
    const result = buildTobitDefaultAnalysis();
    expect(result.rightCensoringEnabled).toBe(false);
  });

  it("method が 'tobit' であること", () => {
    const result = buildTobitDefaultAnalysis();
    expect(result.method).toBe("tobit");
  });
});

// ---------------------------------------------------------------------------
// buildTobitRequestParams
// ---------------------------------------------------------------------------
describe("buildTobitRequestParams", () => {
  it("左打ち切りが有効のとき leftCensoringLimit に値を設定する", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: true,
      leftCensoringLimit: 0,
      rightCensoringEnabled: false,
      rightCensoringLimit: 0,
    });
    expect(result.leftCensoringLimit).toBe(0);
  });

  it("左打ち切りが無効のとき leftCensoringLimit を null にする", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: false,
      leftCensoringLimit: 0,
      rightCensoringEnabled: false,
      rightCensoringLimit: 0,
    });
    expect(result.leftCensoringLimit).toBeNull();
  });

  it("右打ち切りが有効のとき rightCensoringLimit に値を設定する", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: true,
      leftCensoringLimit: 0,
      rightCensoringEnabled: true,
      rightCensoringLimit: 5,
    });
    expect(result.rightCensoringLimit).toBe(5);
  });

  it("右打ち切りが無効のとき rightCensoringLimit を null にする", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: true,
      leftCensoringLimit: 0,
      rightCensoringEnabled: false,
      rightCensoringLimit: 5,
    });
    expect(result.rightCensoringLimit).toBeNull();
  });

  it("左右打ち切りを両方有効にしたとき両方の値を設定する", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: true,
      leftCensoringLimit: 0,
      rightCensoringEnabled: true,
      rightCensoringLimit: 10,
    });
    expect(result.leftCensoringLimit).toBe(0);
    expect(result.rightCensoringLimit).toBe(10);
  });

  it("左右打ち切りを両方無効にしたとき両方 null にする", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: false,
      leftCensoringLimit: 0,
      rightCensoringEnabled: false,
      rightCensoringLimit: 0,
    });
    expect(result.leftCensoringLimit).toBeNull();
    expect(result.rightCensoringLimit).toBeNull();
  });

  it("打ち切り限界に負の値を指定できる（下方打ち切りが負の場合）", () => {
    const result = buildTobitRequestParams({
      method: "tobit",
      leftCensoringEnabled: true,
      leftCensoringLimit: -5,
      rightCensoringEnabled: false,
      rightCensoringLimit: 0,
    });
    expect(result.leftCensoringLimit).toBe(-5);
  });

  it("method が 'tobit' であること", () => {
    const result = buildTobitRequestParams(buildTobitDefaultAnalysis());
    expect(result.method).toBe("tobit");
  });
});
