import { OutputResultFormat } from "@/api/model/outputResultFormat";
import { RegressionOutputOptionsStatInParentheses } from "@/api/model/regressionOutputOptionsStatInParentheses";
import { Button } from "@/components/atoms/Button/Button";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { BaseDialog } from "@/components/molecules/Dialog/BaseDialog";
import { useOutputResult } from "@/hooks/useOutputResult";
import { cn } from "@/lib/utils/helpers";
import type { LinearRegressionResultType } from "@/types/commonTypes";
import * as RadixDialog from "@radix-ui/react-dialog";
import {
  Check,
  ChevronDown,
  ChevronUp,
  Clipboard,
  Loader2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

// ─── 型定義 ──────────────────────────────────────────────────────────────────

type VarEntryType = {
  original: string;
  label: string;
};

export type OutputResultDialogPropsType =
  | {
      open: boolean;
      onOpenChange: (open: boolean) => void;
      resultKind: "regression";
      result: LinearRegressionResultType;
    }
  | {
      open: boolean;
      onOpenChange: (open: boolean) => void;
      resultKind: "descriptive_statistics";
      resultId: string;
      title: string;
    }
  | {
      open: boolean;
      onOpenChange: (open: boolean) => void;
      resultKind: "confidence_interval";
      resultId: string;
      title: string;
    };

type RegressionOutputResultDialogContentPropsType = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: LinearRegressionResultType;
  format: OutputResultFormat;
  setFormat: (value: OutputResultFormat) => void;
  statInParentheses: RegressionOutputOptionsStatInParentheses;
  setStatInParentheses: (
    value: RegressionOutputOptionsStatInParentheses,
  ) => void;
  constAtBottom: boolean;
  setConstAtBottom: (value: boolean) => void;
};

type DescriptiveStatisticsOutputResultDialogContentPropsType = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resultId: string;
  title: string;
  resultType: "descriptive_statistics" | "confidence_interval";
  format: OutputResultFormat;
  setFormat: (value: OutputResultFormat) => void;
};

const createInitialVarEntries = (
  result: LinearRegressionResultType,
): VarEntryType[] =>
  result.parameters.map((parameter) => ({
    original: parameter.variable,
    label: "",
  }));

// ─── コンポーネント ───────────────────────────────────────────────────────────

const RegressionOutputResultDialogContent = ({
  open,
  onOpenChange,
  result,
  format,
  setFormat,
  statInParentheses,
  setStatInParentheses,
  constAtBottom,
  setConstAtBottom,
}: RegressionOutputResultDialogContentPropsType) => {
  const { t } = useTranslation();
  const initialVarEntries = createInitialVarEntries(result);

  // ── 変数エントリー（順序 + ラベル） ──────────────────────────────────────
  const [varEntries, setVarEntries] = useState<VarEntryType[]>(
    () => initialVarEntries,
  );

  // ── ラベル変更をデバウンス（API 呼び出し頻度を抑制） ─────────────────────
  const [debouncedVarEntries, setDebouncedVarEntries] = useState<
    VarEntryType[]
  >(() => initialVarEntries);

  // ── コピー状態 ────────────────────────────────────────────────────────────
  const [isCopied, setIsCopied] = useState(false);

  const { content, isLoading, error, fetchOutput } = useOutputResult();

  // ── varEntries 変更を 600ms デバウンス ────────────────────────────────────
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedVarEntries(varEntries);
    }, 600);
    return () => clearTimeout(timer);
  }, [varEntries]);

  // ── オプション変更時に出力を再フェッチ ───────────────────────────────────
  const debouncedVarEntriesJson = JSON.stringify(debouncedVarEntries);
  useEffect(() => {
    if (!open) return;
    const entries: VarEntryType[] = JSON.parse(debouncedVarEntriesJson);
    const variableLabels = Object.fromEntries(
      entries
        .filter((e) => e.label.trim() !== "")
        .map((e) => [e.original, e.label.trim()]),
    );
    const variableOrder = entries.map((e) => e.original);

    void fetchOutput({
      resultType: "regression",
      resultIds: [result.resultId],
      format,
      options: {
        statInParentheses,
        constAtBottom,
        variableLabels:
          Object.keys(variableLabels).length > 0 ? variableLabels : undefined,
        variableOrder,
      },
    });
  }, [
    open,
    result.resultId,
    format,
    statInParentheses,
    constAtBottom,
    debouncedVarEntriesJson,
    fetchOutput,
  ]);

  // ── 変数操作 ──────────────────────────────────────────────────────────────
  const moveUp = (index: number) => {
    if (index <= 0) return;
    setVarEntries((prev) => {
      const next = [...prev];
      [next[index - 1], next[index]] = [next[index], next[index - 1]];
      return next;
    });
  };

  const moveDown = (index: number) => {
    setVarEntries((prev) => {
      if (index >= prev.length - 1) return prev;
      const next = [...prev];
      [next[index], next[index + 1]] = [next[index + 1], next[index]];
      return next;
    });
  };

  const setLabel = (index: number, label: string) => {
    setVarEntries((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], label };
      return next;
    });
  };

  // ── コピー ────────────────────────────────────────────────────────────────
  const handleCopy = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  // ─── レンダリング ──────────────────────────────────────────────────────────

  return (
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("OutputResultDialog.Title")}
      subtitle={result.dependentVariable}
      maxWidth="2xl"
      footerVariant="none"
    >
      {/* ── 出力オプション ── */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
            {t("OutputResultDialog.Format")}
          </label>
          <Select
            value={format}
            onValueChange={(v) => setFormat(v as OutputResultFormat)}
            data-testid="output-format-select"
          >
            <SelectItem value={OutputResultFormat.text}>
              {t("OutputResultDialog.FormatText")}
            </SelectItem>
            <SelectItem value={OutputResultFormat.markdown}>
              {t("OutputResultDialog.FormatMarkdown")}
            </SelectItem>
            <SelectItem value={OutputResultFormat.latex}>
              {t("OutputResultDialog.FormatLatex")}
            </SelectItem>
          </Select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
            {t("OutputResultDialog.StatInParentheses")}
          </label>
          <Select
            value={statInParentheses}
            onValueChange={(v) =>
              setStatInParentheses(
                v as RegressionOutputOptionsStatInParentheses,
              )
            }
            data-testid="output-stat-select"
          >
            <SelectItem value={RegressionOutputOptionsStatInParentheses.se}>
              {t("OutputResultDialog.StatSE")}
            </SelectItem>
            <SelectItem value={RegressionOutputOptionsStatInParentheses.t}>
              {t("OutputResultDialog.StatT")}
            </SelectItem>
            <SelectItem value={RegressionOutputOptionsStatInParentheses.p}>
              {t("OutputResultDialog.StatP")}
            </SelectItem>
            <SelectItem value={RegressionOutputOptionsStatInParentheses.none}>
              {t("OutputResultDialog.StatNone")}
            </SelectItem>
          </Select>
        </div>
      </div>

      {/* ── 定数項位置 ── */}
      <div className="mb-4 flex items-center gap-2">
        <input
          type="checkbox"
          id="constAtBottom"
          checked={constAtBottom}
          onChange={(e) => setConstAtBottom(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 accent-brand-accent"
          data-testid="output-const-bottom"
        />
        <label
          htmlFor="constAtBottom"
          className="cursor-pointer text-sm text-gray-700 dark:text-gray-300"
        >
          {t("OutputResultDialog.ConstAtBottom")}
        </label>
      </div>

      {/* ── 変数設定（ラベル・順序） ── */}
      <div className="mb-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {t("OutputResultDialog.VariableSettings")}
        </h4>
        <div className="overflow-hidden rounded-md border border-gray-200 dark:border-gray-700">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
                <th className="w-14 px-2 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {t("OutputResultDialog.Order")}
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {t("OutputResultDialog.OriginalName")}
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">
                  {t("OutputResultDialog.DisplayLabel")}
                </th>
              </tr>
            </thead>
            <tbody>
              {varEntries.map((entry, idx) => (
                <tr
                  key={entry.original}
                  className="border-b border-gray-100 last:border-0 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50"
                  data-testid={`var-entry-${entry.original}`}
                >
                  {/* ↑↓ ボタン */}
                  <td className="px-2 py-1">
                    <div className="flex items-center gap-0.5">
                      <button
                        type="button"
                        onClick={() => moveUp(idx)}
                        disabled={idx === 0}
                        className={cn(
                          "rounded p-0.5 text-gray-400 transition-colors hover:text-gray-700 dark:hover:text-gray-200",
                          "disabled:cursor-not-allowed disabled:opacity-25",
                        )}
                        aria-label={`${entry.original} move up`}
                      >
                        <ChevronUp className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => moveDown(idx)}
                        disabled={idx === varEntries.length - 1}
                        className={cn(
                          "rounded p-0.5 text-gray-400 transition-colors hover:text-gray-700 dark:hover:text-gray-200",
                          "disabled:cursor-not-allowed disabled:opacity-25",
                        )}
                        aria-label={`${entry.original} move down`}
                      >
                        <ChevronDown className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>

                  {/* 元の変数名 */}
                  <td className="px-3 py-1.5 font-mono text-xs text-gray-700 dark:text-gray-300">
                    {entry.original}
                  </td>

                  {/* 表示ラベル入力 */}
                  <td className="px-3 py-1.5">
                    <input
                      type="text"
                      value={entry.label}
                      onChange={(e) => setLabel(idx, e.target.value)}
                      placeholder={entry.original}
                      className={cn(
                        "w-full rounded border border-gray-300 px-2 py-1 text-sm",
                        "bg-white dark:bg-gray-900 dark:border-gray-600 dark:text-gray-200 dark:placeholder-gray-500",
                        "focus:outline-none focus:ring-1 focus:ring-gray-500",
                      )}
                      data-testid={`var-label-input-${entry.original}`}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── プレビュー ── */}
      <div className="mb-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {t("OutputResultDialog.Preview")}
        </h4>
        <div className="relative max-h-64 min-h-20 overflow-auto rounded-md border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
          {isLoading && (
            <div className="flex h-20 items-center justify-center gap-2 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("OutputResultDialog.Loading")}
            </div>
          )}
          {error && !isLoading && (
            <div className="flex h-20 items-center justify-center text-sm text-red-500">
              {t("OutputResultDialog.Error")}
            </div>
          )}
          {content && !isLoading && (
            <pre
              className="p-3 text-xs font-mono leading-relaxed whitespace-pre text-gray-800 dark:text-gray-200"
              data-testid="output-preview"
            >
              {content}
            </pre>
          )}
        </div>
      </div>

      {/* ── フッター（コピー + 閉じる） ── */}
      <div className="flex items-center justify-end gap-2 border-t border-gray-100 dark:border-gray-700 pt-3">
        <RadixDialog.Close asChild>
          <Button variant="outline">{t("Common.Close")}</Button>
        </RadixDialog.Close>
        <button
          type="button"
          onClick={() => void handleCopy()}
          disabled={!content || isLoading}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-6 py-2.5 text-sm font-semibold transition-colors cursor-pointer",
            "focus-visible:outline-2 focus-visible:outline-offset-2",
            isCopied
              ? "bg-green-600 text-white focus-visible:outline-green-600"
              : "bg-brand-accent text-white hover:bg-brand-accent/90 focus-visible:outline-brand-accent",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
          data-testid="output-copy-btn"
        >
          {isCopied ? (
            <>
              <Check className="h-4 w-4" />
              {t("OutputResultDialog.Copied")}
            </>
          ) : (
            <>
              <Clipboard className="h-4 w-4" />
              {t("OutputResultDialog.CopyButton")}
            </>
          )}
        </button>
      </div>
    </BaseDialog>
  );
};

// ─── 基本統計量出力ダイアログ内容 ──────────────────────────────────────────────

const DescriptiveStatisticsOutputResultDialogContent = ({
  open,
  onOpenChange,
  resultId,
  title,
  resultType,
  format,
  setFormat,
}: DescriptiveStatisticsOutputResultDialogContentPropsType) => {
  const { t } = useTranslation();
  const [isCopied, setIsCopied] = useState(false);
  const { content, isLoading, error, fetchOutput } = useOutputResult();

  useEffect(() => {
    if (!open) return;
    if (resultType === "descriptive_statistics") {
      void fetchOutput({
        resultType,
        resultIds: [resultId],
        format,
        options: {
          includeResultName: false,
          includeTableName: false,
        },
      });
      return;
    }

    void fetchOutput({
      resultType,
      resultIds: [resultId],
      format,
      options: {
        includeResultName: false,
        includeTableName: false,
        includeConfidenceLevel: true,
      },
    });
  }, [open, resultId, resultType, format, fetchOutput]);

  const handleCopy = async () => {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  return (
    <BaseDialog
      open={open}
      onOpenChange={onOpenChange}
      title={t("OutputResultDialog.Title")}
      subtitle={title}
      maxWidth="2xl"
      footerVariant="none"
    >
      {/* ── 出力フォーマット ── */}
      <div className="mb-4 max-w-xs">
        <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
          {t("OutputResultDialog.Format")}
        </label>
        <Select
          value={format}
          onValueChange={(v) => setFormat(v as OutputResultFormat)}
          data-testid="output-format-select"
        >
          <SelectItem value={OutputResultFormat.text}>
            {t("OutputResultDialog.FormatText")}
          </SelectItem>
          <SelectItem value={OutputResultFormat.markdown}>
            {t("OutputResultDialog.FormatMarkdown")}
          </SelectItem>
          <SelectItem value={OutputResultFormat.latex}>
            {t("OutputResultDialog.FormatLatex")}
          </SelectItem>
        </Select>
      </div>

      {/* ── プレビュー ── */}
      <div className="mb-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {t("OutputResultDialog.Preview")}
        </h4>
        <div className="relative max-h-64 min-h-20 overflow-auto rounded-md border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900">
          {isLoading && (
            <div className="flex h-20 items-center justify-center gap-2 text-sm text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("OutputResultDialog.Loading")}
            </div>
          )}
          {error && !isLoading && (
            <div className="flex h-20 items-center justify-center text-sm text-red-500">
              {t("OutputResultDialog.Error")}
            </div>
          )}
          {content && !isLoading && (
            <pre
              className="p-3 text-xs font-mono leading-relaxed whitespace-pre text-gray-800 dark:text-gray-200"
              data-testid="output-preview"
            >
              {content}
            </pre>
          )}
        </div>
      </div>

      {/* ── フッター ── */}
      <div className="flex items-center justify-end gap-2 border-t border-gray-100 dark:border-gray-700 pt-3">
        <RadixDialog.Close asChild>
          <Button variant="outline">{t("Common.Close")}</Button>
        </RadixDialog.Close>
        <button
          type="button"
          onClick={() => void handleCopy()}
          disabled={!content || isLoading}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md px-6 py-2.5 text-sm font-semibold transition-colors cursor-pointer",
            "focus-visible:outline-2 focus-visible:outline-offset-2",
            isCopied
              ? "bg-green-600 text-white focus-visible:outline-green-600"
              : "bg-brand-accent text-white hover:bg-brand-accent/90 focus-visible:outline-brand-accent",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
          data-testid="output-copy-btn"
        >
          {isCopied ? (
            <>
              <Check className="h-4 w-4" />
              {t("OutputResultDialog.Copied")}
            </>
          ) : (
            <>
              <Clipboard className="h-4 w-4" />
              {t("OutputResultDialog.CopyButton")}
            </>
          )}
        </button>
      </div>
    </BaseDialog>
  );
};

export const OutputResultDialog = (props: OutputResultDialogPropsType) => {
  const [format, setFormat] = useState<OutputResultFormat>(
    OutputResultFormat.markdown,
  );
  const [statInParentheses, setStatInParentheses] =
    useState<RegressionOutputOptionsStatInParentheses>(
      RegressionOutputOptionsStatInParentheses.se,
    );
  const [constAtBottom, setConstAtBottom] = useState(false);

  if (
    props.resultKind === "descriptive_statistics" ||
    props.resultKind === "confidence_interval"
  ) {
    return (
      <DescriptiveStatisticsOutputResultDialogContent
        key={props.resultId}
        open={props.open}
        onOpenChange={props.onOpenChange}
        resultId={props.resultId}
        title={props.title}
        resultType={props.resultKind}
        format={format}
        setFormat={setFormat}
      />
    );
  }

  return (
    <RegressionOutputResultDialogContent
      key={props.result.resultId}
      open={props.open}
      onOpenChange={props.onOpenChange}
      result={props.result}
      format={format}
      setFormat={setFormat}
      statInParentheses={statInParentheses}
      setStatInParentheses={setStatInParentheses}
      constAtBottom={constAtBottom}
      setConstAtBottom={setConstAtBottom}
    />
  );
};
