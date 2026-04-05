/**
 * useOutputResult のテスト
 *
 * - fetchOutput 呼び出し成功時に content が設定され isLoading=false になる
 * - fetchOutput 呼び出し中は isLoading=true になる
 * - fetchOutput 呼び出し失敗時に error がセットされる
 */
import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getEconomiconAppAPI } from "../api/endpoints";
import { OutputResultRequestFormat } from "../api/model/outputResultRequestFormat";
import { OutputResultRequestStatInParentheses } from "../api/model/outputResultRequestStatInParentheses";
import { useOutputResult } from "./useOutputResult";

vi.mock("../api/endpoints", () => ({
  getEconomiconAppAPI: vi.fn(),
}));

const mockOutputResult = vi.fn();

beforeEach(() => {
  vi.mocked(getEconomiconAppAPI).mockReturnValue({
    outputResult: mockOutputResult,
  } as never);
  mockOutputResult.mockReset();
});

const baseRequest = {
  resultIds: ["result-1"],
  format: OutputResultRequestFormat.markdown,
  statInParentheses: OutputResultRequestStatInParentheses.se,
  constAtBottom: false,
  variableOrder: ["x1", "const"],
};

describe("useOutputResult", () => {
  it("test_useOutputResult_success: 成功時に content が設定され isLoading=false になる", async () => {
    mockOutputResult.mockResolvedValueOnce({
      code: "OK",
      result: { content: "| x1 | 0.5 |", format: "markdown" },
    });

    const { result } = renderHook(() => useOutputResult());

    expect(result.current.isLoading).toBe(false);
    expect(result.current.content).toBeNull();

    await act(async () => {
      await result.current.fetchOutput(baseRequest);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.content).toBe("| x1 | 0.5 |");
    expect(result.current.error).toBeNull();
  });

  it("test_useOutputResult_loading: fetchOutput 呼び出し開始直後は isLoading=true になる", async () => {
    let resolvePromise!: () => void;
    mockOutputResult.mockReturnValueOnce(
      new Promise((resolve) => {
        resolvePromise = () =>
          resolve({
            code: "OK",
            result: { content: "text", format: "text" },
          });
      }),
    );

    const { result } = renderHook(() => useOutputResult());

    let fetchPromise!: Promise<void>;
    act(() => {
      fetchPromise = result.current.fetchOutput(baseRequest);
    });

    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePromise();
      await fetchPromise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  it("test_useOutputResult_error: API 失敗時に error がセットされる", async () => {
    mockOutputResult.mockRejectedValueOnce(new Error("接続失敗"));

    const { result } = renderHook(() => useOutputResult());

    await act(async () => {
      await result.current.fetchOutput(baseRequest);
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.content).toBeNull();
    expect(result.current.error).toBe("接続失敗");
  });

  it("test_useOutputResult_nonOkCode: code が OK 以外の場合も error がセットされる", async () => {
    mockOutputResult.mockResolvedValueOnce({
      code: "NG",
      message: "バリデーションエラー",
      result: null,
    });

    const { result } = renderHook(() => useOutputResult());

    await act(async () => {
      await result.current.fetchOutput(baseRequest);
    });

    expect(result.current.error).toBe("error");
    expect(result.current.content).toBeNull();
  });
});
