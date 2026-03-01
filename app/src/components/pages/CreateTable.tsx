/**
 * テーブル作成ページ
 *
 * - テーブル名 / 行数を TanStack Form で管理
 * - 列リストはローカル state で管理（↑↓で並べ替え、× で削除）
 * - Enter で列を次々と追加し、入力欄にフォーカスを戻す
 * - API 成功後はテーブルを即時アクティブ化して DataPreview に遷移
 */
import { useForm, useStore } from "@tanstack/react-form";
import { ArrowDown, ArrowUp, Plus, X } from "lucide-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
} from "../../lib/utils/apiError";
import { getTableInfo } from "../../lib/utils/internal";
import { useCurrentPageStore } from "../../stores/currentView";
import { useTableInfosStore } from "../../stores/tableInfos";
import { useTableListStore } from "../../stores/tableList";
import { Button } from "../atoms/Button/Button";
import { InputText } from "../atoms/Input/InputText";
import { ErrorAlert } from "../molecules/Alert/ErrorAlert";
import { FormField } from "../molecules/Form/FormField";
import { PageLayout } from "../templates/PageLayout";

type ColumnEntry = { id: string; name: string };

let _nextId = 1;
const nextId = () => String(_nextId++);

export const CreateTable = () => {
  const { t } = useTranslation();
  const setCurrentView = useCurrentPageStore((s) => s.setCurrentView);
  const addTableName = useTableListStore((s) => s.addTableName);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);

  const [columns, setColumns] = useState<ColumnEntry[]>([]);
  const [newColName, setNewColName] = useState("");
  const [colError, setColError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const newColRef = useRef<HTMLInputElement>(null);

  const hasControlChars = (s: string) =>
    s.split("").some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127);

  const addColumn = () => {
    const trimmed = newColName.trim();
    if (!trimmed) return;
    if (hasControlChars(trimmed)) {
      setColError(t("CreateTableView.ColumnNameInvalidChars"));
      return;
    }
    if (columns.some((c) => c.name === trimmed)) {
      setColError(t("CreateTableView.ColumnNameDuplicate"));
      return;
    }
    setColumns((prev) => [...prev, { id: nextId(), name: trimmed }]);
    setNewColName("");
    setColError(null);
    setTimeout(() => newColRef.current?.focus(), 0);
  };

  const removeColumn = (id: string) =>
    setColumns((prev) => prev.filter((c) => c.id !== id));

  const moveUp = (idx: number) => {
    if (idx === 0) return;
    setColumns((prev) => {
      const next = [...prev];
      [next[idx - 1], next[idx]] = [next[idx], next[idx - 1]];
      return next;
    });
  };

  const moveDown = (idx: number) => {
    setColumns((prev) => {
      if (idx >= prev.length - 1) return prev;
      const next = [...prev];
      [next[idx], next[idx + 1]] = [next[idx + 1], next[idx]];
      return next;
    });
  };

  const form = useForm({
    defaultValues: { tableName: "", rowCount: 1000 },
    validators: {
      onSubmit: z.object({
        tableName: z
          .string()
          .min(1, t("ValidationMessages.TableNameRequired"))
          .max(128, t("ValidationMessages.TableNameTooLong"))
          .refine(
            (v) => !hasControlChars(v),
            t("ValidationMessages.TableNameInvalidChars"),
          ),
        rowCount: z.number().min(1, t("ValidationMessages.NumRowsMoreThan0")),
      }),
    },
    onSubmit: async ({ value }) => {
      if (columns.length === 0) {
        setColError(t("CreateTableView.ColumnRequired"));
        return;
      }
      setColError(null);
      setApiError(null);

      try {
        const response = await getEconomiconAPI().createTable({
          tableName: value.tableName,
          rowCount: value.rowCount,
          columnNames: columns.map((c) => c.name),
        });

        if (response.code === "OK") {
          const info = await getTableInfo(value.tableName);
          addTableName(value.tableName);
          addTableInfo(info); // 内部で activeTableName を更新してアクティブ化
          setCurrentView("DataPreview");
        } else {
          setApiError(
            getResponseErrorMessage(response, t("Error.UnexpectedError")),
          );
        }
      } catch (error) {
        setApiError(extractApiErrorMessage(error, t("Error.UnexpectedError")));
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  return (
    <PageLayout
      title={t("CreateTableView.Title")}
      description={t("CreateTableView.Description")}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          e.stopPropagation();
          void form.handleSubmit();
        }}
        className="flex flex-col gap-6 mt-2"
      >
        {/* テーブル基本設定 */}
        <div className="grid grid-cols-2 gap-4">
          <form.Field
            name="tableName"
            validators={{
              onChange: ({ value }) => {
                if (!value.trim())
                  return t("ValidationMessages.TableNameRequired");
                if (value.length > 128)
                  return t("ValidationMessages.TableNameTooLong");
                if (hasControlChars(value))
                  return t("ValidationMessages.TableNameInvalidChars");
                return undefined;
              },
            }}
          >
            {(field) => {
              const errorMsg = field.state.meta.isTouched
                ? (field.state.meta.errors[0] as string | undefined)
                : undefined;
              return (
                <FormField
                  label={t("CreateTableView.TableName")}
                  htmlFor="ct-table-name"
                  error={errorMsg}
                >
                  <InputText
                    id="ct-table-name"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    onBlur={field.handleBlur}
                    placeholder={t("CreateTableView.TableNamePlaceholder")}
                    disabled={isSubmitting}
                    autoFocus
                  />
                </FormField>
              );
            }}
          </form.Field>

          <form.Field
            name="rowCount"
            validators={{
              onChange: ({ value }) =>
                value < 1
                  ? t("ValidationMessages.NumRowsMoreThan0")
                  : undefined,
            }}
          >
            {(field) => {
              const errorMsg = field.state.meta.isTouched
                ? (field.state.meta.errors[0] as string | undefined)
                : undefined;
              return (
                <FormField
                  label={t("CreateTableView.RowCount")}
                  htmlFor="ct-row-count"
                  error={errorMsg}
                >
                  <InputText
                    id="ct-row-count"
                    type="number"
                    value={String(field.state.value)}
                    onChange={(e) => field.handleChange(Number(e.target.value))}
                    onBlur={field.handleBlur}
                    disabled={isSubmitting}
                  />
                </FormField>
              );
            }}
          </form.Field>
        </div>

        {/* 列定義セクション */}
        <div className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {t("CreateTableView.ColumnsSection")}
            {columns.length > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-400">
                {t("CreateTableView.ColumnsCount", { count: columns.length })}
              </span>
            )}
          </h2>

          {/* 列リスト */}
          {columns.length > 0 && (
            <ul className="flex flex-col rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              {columns.map((col, idx) => (
                <li
                  key={col.id}
                  className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border-b last:border-b-0 border-gray-100 dark:border-gray-700"
                >
                  {/* 順序変更ボタン */}
                  <div className="flex flex-col gap-0.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => moveUp(idx)}
                      disabled={idx === 0 || isSubmitting}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-25 disabled:cursor-not-allowed focus:outline-none"
                      aria-label={t("CreateTableView.MoveUp")}
                    >
                      <ArrowUp className="size-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => moveDown(idx)}
                      disabled={idx === columns.length - 1 || isSubmitting}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 disabled:opacity-25 disabled:cursor-not-allowed focus:outline-none"
                      aria-label={t("CreateTableView.MoveDown")}
                    >
                      <ArrowDown className="size-3" />
                    </button>
                  </div>

                  {/* 連番 */}
                  <span className="text-xs text-gray-400 w-5 text-right shrink-0 tabular-nums">
                    {idx + 1}
                  </span>

                  {/* 列名 */}
                  <span className="flex-1 text-sm font-mono text-gray-800 dark:text-gray-200 truncate">
                    {col.name}
                  </span>

                  {/* 削除ボタン */}
                  <button
                    type="button"
                    onClick={() => removeColumn(col.id)}
                    disabled={isSubmitting}
                    className="shrink-0 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors disabled:cursor-not-allowed focus:outline-none"
                    aria-label={t("CreateTableView.RemoveColumn")}
                  >
                    <X className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* 列追加インプット */}
          <div className="flex gap-2">
            <div className="flex-1">
              <InputText
                ref={newColRef}
                value={newColName}
                onChange={(e) => {
                  setNewColName(e.target.value);
                  if (colError) setColError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addColumn();
                  }
                }}
                placeholder={t("CreateTableView.NewColumnPlaceholder")}
                disabled={isSubmitting}
              />
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={addColumn}
              disabled={isSubmitting || !newColName.trim()}
              className="shrink-0 gap-1.5"
            >
              <Plus className="size-4" />
              {t("CreateTableView.AddColumn")}
            </Button>
          </div>

          {/* 列エラー */}
          {colError && (
            <p className="text-xs text-red-500 dark:text-red-400">{colError}</p>
          )}
        </div>

        {/* API エラー */}
        {apiError && <ErrorAlert message={apiError} />}

        {/* アクションバー */}
        <div className="shrink-0 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCurrentView("ImportDataFile")}
              disabled={isSubmitting}
            >
              {t("Common.Cancel")}
            </Button>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              {isSubmitting ? "..." : t("CreateTableView.Submit")}
            </Button>
          </div>
        </div>
      </form>
    </PageLayout>
  );
};
