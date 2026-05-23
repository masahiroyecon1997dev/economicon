import { z } from "zod";
import {
  importFileBodyTableNameMax,
  importFileBodyTableNameRegExp,
} from "@/api/zod/data/data";

/**
 * バックエンド api/economicon/models/types.py の制約を移植した
 * インポートダイアログ用 Zod スキーマ
 *
 * NAME_PATTERN = r"^[^\x00-\x1f\x7f]+$"  (制御文字・DEL 禁止)
 * Separator: min_length=1, max_length=10
 * ExcelSheetName: max_length=31, pattern=^[^\/\\\?\*\:\[\]]+$, 先頭末尾 ' 禁止
 * CsvEncoding: "utf8" | "latin1" | "ascii" | "gbk" | "windows-1252" | "shift_jis"
 */

export const CSV_ENCODINGS = [
  "utf8",
  "latin1",
  "ascii",
  "gbk",
  "windows-1252",
  "shift_jis",
] as const;

export type CsvEncoding = (typeof CSV_ENCODINGS)[number];

export type SeparatorMode = "comma" | "tab" | "other";

/** ファイル種別（ダイアログの表示切替用） */
export type ImportFileType = "csv" | "excel" | "parquet" | "other";

export const getImportFileType = (fileName: string): ImportFileType => {
  const lower = fileName.toLowerCase();
  if (lower.endsWith(".csv") || lower.endsWith(".tsv")) return "csv";
  if (lower.endsWith(".xlsx") || lower.endsWith(".xls")) return "excel";
  if (lower.endsWith(".parquet")) return "parquet";
  return "other";
};

export const createImportConfigSchema = (t: (key: string) => string) =>
  z.object({
    tableName: z
      .string()
      .min(1, t("ValidationMessages.DataNameRequired"))
      .max(importFileBodyTableNameMax, t("ValidationMessages.DataNameTooLong"))
      .regex(
        importFileBodyTableNameRegExp,
        t("ValidationMessages.DataNameInvalidChars"),
      ),
    // CSV 専用
    separatorMode: z.enum(["comma", "tab", "other"] as const).default("comma"),
    separatorCustom: z.string().default(""),
    encoding: z.enum(CSV_ENCODINGS).default("utf8"),
    // Excel 専用
    sheetName: z.string().default(""),
  });

/**
 * 区切り文字（その他）フィールドのバリデーション
 * separatorMode が "other" の場合のみチェックする
 */
export const validateSeparatorCustom = (
  value: string,
  mode: SeparatorMode,
  t: (key: string) => string,
): string | undefined => {
  if (mode !== "other") return undefined;
  if (value.length === 0) return t("ValidationMessages.SeparatorRequired");
  if (value.length > 10) return t("ValidationMessages.SeparatorTooLong");
  return undefined;
};

/**
 * Excel シート名フィールドのバリデーション（省略可能）
 */
export const validateSheetName = (
  value: string,
  t: (key: string) => string,
): string | undefined => {
  if (value.length === 0) return undefined;
  if (value.length > 31) return t("ValidationMessages.SheetNameTooLong");
  if (/[/\\?*:[\]]/.test(value))
    return t("ValidationMessages.SheetNameInvalidChars");
  if (value.startsWith("'") || value.endsWith("'"))
    return t("ValidationMessages.SheetNameInvalidQuotes");
  return undefined;
};

/** onImport コールバックに渡す設定型 */
export type ImportConfigSettings = {
  tableName: string;
  separator?: string;
  encoding?: string;
  sheetName?: string;
};

/** フォーム値から API 呼び出し用設定を生成 */
export const resolveImportSettings = (
  values: z.infer<ReturnType<typeof createImportConfigSchema>>,
  fileType: ImportFileType,
): ImportConfigSettings => {
  const settings: ImportConfigSettings = {
    tableName: values.tableName.trim(),
  };
  if (fileType === "csv") {
    const sep =
      values.separatorMode === "comma"
        ? ","
        : values.separatorMode === "tab"
          ? "\t"
          : values.separatorCustom;
    settings.separator = sep;
    settings.encoding = values.encoding;
  }
  if (fileType === "excel" && values.sheetName.trim().length > 0) {
    settings.sheetName = values.sheetName.trim();
  }
  return settings;
};
