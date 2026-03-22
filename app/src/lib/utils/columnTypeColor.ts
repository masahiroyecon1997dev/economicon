/**
 * Polars 型に対応した色・ラベル設定を返すユーティリティ
 *
 * 型バッジ・列リスト・ヘッダーなど複数箇所で使用する共通ロジック
 */

export type ColumnTypeColorResult = {
  bg: string;
  text: string;
  label: string;
};

/**
 * Polars の型文字列から表示用カラー設定を返す
 *
 * @param type - Polars 型文字列 (例: "Int64", "Float64", "Utf8", "Date")
 */
export const getPolarsTypeColor = (type: string): ColumnTypeColorResult => {
  if (type.includes("Int") || type.includes("UInt")) {
    return {
      bg: "bg-blue-100 dark:bg-blue-900/30",
      text: "text-blue-700 dark:text-blue-300",
      label: "#",
    };
  } else if (type.includes("Float")) {
    return {
      bg: "bg-green-100 dark:bg-green-900/30",
      text: "text-green-700 dark:text-green-300",
      label: "1.2",
    };
  } else if (type.includes("Utf8") || type.includes("String")) {
    return {
      bg: "bg-purple-100 dark:bg-purple-900/30",
      text: "text-purple-700 dark:text-purple-300",
      label: "ABC",
    };
  } else if (type.includes("Date") || type.includes("Datetime")) {
    return {
      bg: "bg-orange-100 dark:bg-orange-900/30",
      text: "text-orange-700 dark:text-orange-300",
      label: "DATE",
    };
  } else if (type.includes("Boolean") || type.includes("Bool")) {
    return {
      bg: "bg-amber-100 dark:bg-amber-900/30",
      text: "text-amber-700 dark:text-amber-300",
      label: "T/F",
    };
  } else {
    return {
      bg: "bg-gray-100 dark:bg-gray-900/30",
      text: "text-gray-700 dark:text-gray-300",
      label: "?",
    };
  }
};
