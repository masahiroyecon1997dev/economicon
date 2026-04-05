/**
 * useFormSubmitting のテスト
 *
 * - isSubmitting が false のとき onIsSubmittingChange(false) が呼ばれる（mount 時）
 * - isSubmitting が true に変化すると onIsSubmittingChange(true) が呼ばれる
 * - onIsSubmittingChange が変わっても isSubmitting が変化しなければ再呼び出しされない
 */
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useFormSubmitting } from "./useFormSubmitting";

describe("useFormSubmitting", () => {
  it("mount 時に isSubmitting=false で onIsSubmittingChange が呼ばれる", () => {
    const cb = vi.fn();
    renderHook(() => useFormSubmitting(false, cb));
    expect(cb).toHaveBeenCalledWith(false);
    expect(cb).toHaveBeenCalledTimes(1);
  });

  it("isSubmitting が true に変化すると onIsSubmittingChange(true) が呼ばれる", () => {
    const cb = vi.fn();
    const { rerender } = renderHook(
      ({ isSubmitting }: { isSubmitting: boolean }) =>
        useFormSubmitting(isSubmitting, cb),
      { initialProps: { isSubmitting: false } },
    );

    cb.mockClear();
    rerender({ isSubmitting: true });
    expect(cb).toHaveBeenCalledWith(true);
    expect(cb).toHaveBeenCalledTimes(1);
  });

  it("isSubmitting が変化しなければ onIsSubmittingChange は再呼び出しされない", () => {
    const cb = vi.fn();
    const { rerender } = renderHook(
      ({ isSubmitting }: { isSubmitting: boolean }) =>
        useFormSubmitting(isSubmitting, cb),
      { initialProps: { isSubmitting: false } },
    );

    cb.mockClear();
    // isSubmitting を変えずに再レンダー
    rerender({ isSubmitting: false });
    expect(cb).not.toHaveBeenCalled();
  });

  it("false → true → false と変化するたびに対応する値で呼ばれる", () => {
    const cb = vi.fn();
    const { rerender } = renderHook(
      ({ isSubmitting }: { isSubmitting: boolean }) =>
        useFormSubmitting(isSubmitting, cb),
      { initialProps: { isSubmitting: false } },
    );

    cb.mockClear();
    rerender({ isSubmitting: true });
    rerender({ isSubmitting: false });
    expect(cb).toHaveBeenNthCalledWith(1, true);
    expect(cb).toHaveBeenNthCalledWith(2, false);
    expect(cb).toHaveBeenCalledTimes(2);
  });
});
