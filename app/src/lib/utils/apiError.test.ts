/**
 * apiError ユーティリティのテスト
 */
import { describe, expect, it } from "vitest";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "@/lib/utils/apiError";

// ---------------------------------------------------------------------------
// getResponseErrorMessage
// ---------------------------------------------------------------------------
describe("getResponseErrorMessage", () => {
  it("message フィールドがある場合はそれを返す", () => {
    expect(
      getResponseErrorMessage({ message: "列名が重複しています" }, "fallback"),
    ).toBe("列名が重複しています");
  });

  it("message がない場合は fallback を返す", () => {
    expect(getResponseErrorMessage({ code: "ERROR" }, "予期しないエラー")).toBe(
      "予期しないエラー",
    );
  });

  it("空オブジェクトでも fallback を返す", () => {
    expect(getResponseErrorMessage({}, "予期しないエラー")).toBe(
      "予期しないエラー",
    );
  });
});

// ---------------------------------------------------------------------------
// extractApiErrorMessage
// ---------------------------------------------------------------------------
describe("extractApiErrorMessage", () => {
  it("Error インスタンスの message を返す", () => {
    expect(
      extractApiErrorMessage(new Error("接続タイムアウト"), "fallback"),
    ).toBe("接続タイムアウト");
  });

  it("文字列として throw された場合はそれを返す", () => {
    expect(extractApiErrorMessage("サーバーエラー", "fallback")).toBe(
      "サーバーエラー",
    );
  });

  it("JSON 文字列の場合は message フィールドを取り出す", () => {
    const json = JSON.stringify({ message: "バリデーションエラー" });
    expect(extractApiErrorMessage(json, "fallback")).toBe(
      "バリデーションエラー",
    );
  });

  it("message を持たない JSON の場合は生の文字列を返す", () => {
    const json = JSON.stringify({ code: "UNKNOWN" });
    expect(extractApiErrorMessage(json, "fallback")).toBe(json);
  });

  it("不明な型の場合は fallback を返す", () => {
    expect(extractApiErrorMessage(42, "fallback")).toBe("fallback");
    expect(extractApiErrorMessage({}, "fallback")).toBe("fallback");
  });
});

// ---------------------------------------------------------------------------
// replaceParamNames
// ---------------------------------------------------------------------------
describe("replaceParamNames", () => {
  it("paramMap の全エントリを置換する", () => {
    expect(
      replaceParamNames("newColumnName は必須です", {
        newColumnName: "新しい列名",
      }),
    ).toBe("新しい列名 は必須です");
  });

  it("複数のパラメータを置換する", () => {
    expect(
      replaceParamNames("sourceColumn と newColumnName が重複しています", {
        sourceColumn: "元の列名",
        newColumnName: "新しい列名",
      }),
    ).toBe("元の列名 と 新しい列名 が重複しています");
  });

  it("一致するパラメータがない場合はそのまま返す", () => {
    expect(replaceParamNames("エラーが発生しました", { foo: "bar" })).toBe(
      "エラーが発生しました",
    );
  });

  it("paramMap が空の場合はそのまま返す", () => {
    expect(replaceParamNames("エラー", {})).toBe("エラー");
  });
});

// ---------------------------------------------------------------------------
// buildResponseErrorMessage
// ---------------------------------------------------------------------------
describe("buildResponseErrorMessage", () => {
  it("response.message を paramMap で置換して返す", () => {
    expect(
      buildResponseErrorMessage(
        { message: "newColumnName はすでに存在します" },
        "fallback",
        { newColumnName: "新しい列名" },
      ),
    ).toBe("新しい列名 はすでに存在します");
  });

  it("message がない場合は fallback を paramMap で置換して返す", () => {
    expect(
      buildResponseErrorMessage({}, "newColumnName のフォールバック", {
        newColumnName: "新しい列名",
      }),
    ).toBe("新しい列名 のフォールバック");
  });

  it("paramMap を省略した場合はそのままのメッセージを返す", () => {
    expect(
      buildResponseErrorMessage(
        { message: "エラーが発生しました" },
        "fallback",
      ),
    ).toBe("エラーが発生しました");
  });
});

// ---------------------------------------------------------------------------
// buildCaughtErrorMessage
// ---------------------------------------------------------------------------
describe("buildCaughtErrorMessage", () => {
  it("throw された Error の message を paramMap で置換して返す", () => {
    expect(
      buildCaughtErrorMessage(
        new Error("newColumnName はすでに存在します"),
        "fallback",
        { newColumnName: "新しい列名" },
      ),
    ).toBe("新しい列名 はすでに存在します");
  });

  it("JSON 文字列の場合は message フィールドを paramMap で置換して返す", () => {
    const json = JSON.stringify({ message: "sourceColumn が見つかりません" });
    expect(
      buildCaughtErrorMessage(json, "fallback", {
        sourceColumn: "元の列名",
      }),
    ).toBe("元の列名 が見つかりません");
  });

  it("paramMap を省略した場合はそのままのメッセージを返す", () => {
    expect(
      buildCaughtErrorMessage(new Error("接続タイムアウト"), "fallback"),
    ).toBe("接続タイムアウト");
  });

  it("不明な型の場合は fallback を paramMap で置換して返す", () => {
    expect(
      buildCaughtErrorMessage(42, "newColumnName のフォールバック", {
        newColumnName: "新しい列名",
      }),
    ).toBe("新しい列名 のフォールバック");
  });
});
