/**
 * フィルタフォーム
 *
 * 列メニューから起動。選択列を初期値として最大 2 条件で
 * テーブルをフィルタリングし、新テーブルとして保存する。
 */
import { useForm, useStore } from "@tanstack/react-form";
import { Plus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import type { FilterOperatorType } from "../../../../api/model";
import { LogicalOperatorType } from "../../../../api/model";
import { FilterTableBody } from "../../../../api/zod/table/table";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
import {
  createFieldError,
  extractFieldError,
} from "../../../../lib/utils/formHelpers";
import { getTableInfo } from "../../../../lib/utils/internal";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { Select, SelectItem } from "../../../atoms/Input/Select";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import type { ColumnOperationFormPropsType } from "./types";

const ALL_OPERATORS: FilterOperatorType[] = [
  "equals",
  "notEquals",
  "greaterThan",
  "greaterThanOrEquals",
  "lessThan",
  "lessThanOrEquals",
];

/** 文字列を可能な限り数値に変換してAPIへ送る */
const toCompareValue = (v: string): string | number => {
  const n = Number(v);
  return v.trim() !== "" && !isNaN(n) ? n : v;
};

export const FilterColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const tErr = createFieldError(t);
  const [apiError, setApiError] = useState<string | null>(null);
  const [hasSecondCondition, setHasSecondCondition] = useState(false);

  const addTableName = useTableListStore((s) => s.addTableName);
  const addTableInfo = useTableInfosStore((s) => s.addTableInfo);

  const allColumns = useTableInfosStore((s) => {
    const info = s.tableInfos.find((info) => info.tableName === tableName);
    return info?.columnList ?? [];
  });

  const form = useForm({
    defaultValues: {
      newTableName: `${tableName}_filtered`,
      logicalOperator:
        LogicalOperatorType.and as (typeof LogicalOperatorType)[keyof typeof LogicalOperatorType],
      c1Column: column.name,
      c1Operator: "equals" as FilterOperatorType,
      c1Value: "",
      c2Column: column.name,
      c2Operator: "equals" as FilterOperatorType,
      c2Value: "",
    },
    validators: {
      onSubmit: FilterTableBody.pick({
        newTableName: true,
        logicalOperator: true,
      })
        .required()
        .merge(
          z.object({
            c1Column: z.string(),
            c1Operator: z.enum([
              "equals",
              "notEquals",
              "greaterThan",
              "greaterThanOrEquals",
              "lessThan",
              "lessThanOrEquals",
            ]),
            c1Value: z.string(),
            c2Column: z.string(),
            c2Operator: z.enum([
              "equals",
              "notEquals",
              "greaterThan",
              "greaterThanOrEquals",
              "lessThan",
              "lessThanOrEquals",
            ]),
            c2Value: z.string(),
          }),
        ),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);

      const conditions: {
        columnName: string;
        condition: FilterOperatorType;
        isCompareColumn: boolean;
        compareValue: string | number;
      }[] = [
        {
          columnName: value.c1Column,
          condition: value.c1Operator,
          isCompareColumn: false,
          compareValue: toCompareValue(value.c1Value),
        },
      ];

      if (hasSecondCondition) {
        conditions.push({
          columnName: value.c2Column,
          condition: value.c2Operator,
          isCompareColumn: false,
          compareValue: toCompareValue(value.c2Value),
        });
      }

      try {
        const response = await getEconomiconAppAPI().filterTable({
          tableName,
          newTableName: value.newTableName,
          logicalOperator: hasSecondCondition
            ? value.logicalOperator
            : LogicalOperatorType.and,
          conditions,
        });

        if (response.code === "OK") {
          const newTableInfo = await getTableInfo(response.result.tableName);
          addTableName(response.result.tableName);
          addTableInfo(newTableInfo);
          onSuccess(allColumns);
        } else {
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                newTableName: t("FilterColumnForm.NewTableName"),
                tableName: t("FilterColumnForm.TableLabel"),
                columnName: t("FilterColumnForm.ColumnName"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(extractApiErrorMessage(error, t("Error.UnexpectedError")));
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);

  return (
    <form
      id={formId}
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
      className="space-y-4"
    >
      {/* 新テーブル名 */}
      <form.Field
        name="newTableName"
        validators={{
          onChange: z.string().min(1, t("ValidationMessages.DataNameRequired")),
        }}
      >
        {(field) => {
          const err = field.state.meta.isTouched
            ? tErr(
                field.state.meta.errors,
                "ValidationMessages.DataNameRequired",
              )
            : undefined;
          return (
            <FormField
              label={t("FilterColumnForm.NewTableName")}
              htmlFor="filter-new-table-name"
              error={err}
            >
              <InputText
                id="filter-new-table-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("FilterColumnForm.NewTableNamePlaceholder")}
                disabled={isSubmitting}
                error={err}
              />
            </FormField>
          );
        }}
      </form.Field>

      {/* 条件 1 */}
      <ConditionBlock
        label={t("FilterColumnForm.Condition1")}
        colFieldName="c1Column"
        opFieldName="c1Operator"
        valFieldName="c1Value"
        colId="filter-c1-col"
        opId="filter-c1-op"
        valId="filter-c1-val"
        required
        allColumns={allColumns}
        form={form}
        isSubmitting={isSubmitting}
        autoFocusValue
        t={t}
      />

      {/* 条件追加ボタン / 条件2 */}
      {!hasSecondCondition ? (
        <Button
          type="button"
          variant="outline"
          onClick={() => setHasSecondCondition(true)}
          disabled={isSubmitting}
          className="w-full flex items-center justify-center gap-1.5"
          data-testid="filter-add-condition"
        >
          <Plus className="h-3.5 w-3.5" />
          {t("FilterColumnForm.AddCondition")}
        </Button>
      ) : (
        <>
          {/* 論理演算子 */}
          <form.Field name="logicalOperator">
            {(field) => (
              <FormField
                label={t("FilterColumnForm.LogicalOperator")}
                htmlFor="filter-logical-op"
              >
                <Select
                  id="filter-logical-op"
                  value={field.state.value}
                  onValueChange={(v) =>
                    field.handleChange(v as typeof LogicalOperatorType.and)
                  }
                  disabled={isSubmitting}
                >
                  <SelectItem value={LogicalOperatorType.and}>
                    {t("FilterColumnForm.And")}
                  </SelectItem>
                  <SelectItem value={LogicalOperatorType.or}>
                    {t("FilterColumnForm.Or")}
                  </SelectItem>
                </Select>
              </FormField>
            )}
          </form.Field>

          {/* 条件 2 */}
          <ConditionBlock
            label={t("FilterColumnForm.Condition2")}
            colFieldName="c2Column"
            opFieldName="c2Operator"
            valFieldName="c2Value"
            colId="filter-c2-col"
            opId="filter-c2-op"
            valId="filter-c2-val"
            required={hasSecondCondition}
            allColumns={allColumns}
            form={form}
            isSubmitting={isSubmitting}
            autoFocusValue={false}
            t={t}
            onRemove={() => setHasSecondCondition(false)}
            removeLabel={t("FilterColumnForm.RemoveCondition")}
          />
        </>
      )}

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};

// ---------------------------------------------------------------------------
// 条件ブロック（再利用）
// ---------------------------------------------------------------------------
type ConditionBlockProps = {
  label: string;
  colFieldName: "c1Column" | "c2Column";
  opFieldName: "c1Operator" | "c2Operator";
  valFieldName: "c1Value" | "c2Value";
  colId: string;
  opId: string;
  valId: string;
  required?: boolean;
  allColumns: { name: string; type: string }[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  form: any;
  isSubmitting: boolean;
  autoFocusValue: boolean;
  t: (key: string) => string;
  onRemove?: () => void;
  removeLabel?: string;
};

const ConditionBlock = ({
  label,
  colFieldName,
  opFieldName,
  valFieldName,
  colId,
  opId,
  valId,
  required = false,
  allColumns,
  form,
  isSubmitting,
  autoFocusValue,
  t,
  onRemove,
  removeLabel,
}: ConditionBlockProps) => (
  <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-3">
    <div className="flex items-center justify-between">
      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        {label}
      </p>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="rounded p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-40"
          aria-label={removeLabel}
          disabled={isSubmitting}
          data-testid="filter-remove-condition"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>

    <div className="grid grid-cols-3 gap-2">
      {/* 列名 */}
      <form.Field name={colFieldName}>
        {(field: {
          state: { value: string };
          handleChange: (v: string) => void;
        }) => (
          <FormField label={t("FilterColumnForm.ColumnName")} htmlFor={colId}>
            <Select
              id={colId}
              value={field.state.value}
              onValueChange={field.handleChange}
              disabled={isSubmitting}
            >
              {allColumns.map((c) => (
                <SelectItem key={c.name} value={c.name}>
                  {c.name}
                </SelectItem>
              ))}
            </Select>
          </FormField>
        )}
      </form.Field>

      {/* 演算子 */}
      <form.Field name={opFieldName}>
        {(field: {
          state: { value: string };
          handleChange: (v: FilterOperatorType) => void;
        }) => (
          <FormField label={t("FilterColumnForm.Operator")} htmlFor={opId}>
            <Select
              id={opId}
              value={field.state.value}
              onValueChange={(v) => field.handleChange(v as FilterOperatorType)}
              disabled={isSubmitting}
            >
              {ALL_OPERATORS.map((op) => (
                <SelectItem key={op} value={op}>
                  {t(`FilterColumnForm.operators.${op}`)}
                </SelectItem>
              ))}
            </Select>
          </FormField>
        )}
      </form.Field>

      {/* 比較値 */}
      <form.Field
        name={valFieldName}
        validators={{
          onChange: ({ value }: { value: string }) =>
            required && !value.trim()
              ? t("FilterColumnForm.ConditionValueRequired")
              : undefined,
        }}
      >
        {(field: {
          state: {
            value: string;
            meta: { errors: unknown[]; isTouched: boolean };
          };
          handleChange: (v: string) => void;
          handleBlur: () => void;
        }) => {
          const errorMsg = field.state.meta.isTouched
            ? extractFieldError(field.state.meta.errors)
            : undefined;
          return (
            <FormField
              label={t("FilterColumnForm.CompareValue")}
              htmlFor={valId}
              error={errorMsg}
            >
              <InputText
                id={valId}
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                disabled={isSubmitting}
                autoFocus={autoFocusValue}
                error={errorMsg}
              />
            </FormField>
          );
        }}
      </form.Field>
    </div>
  </div>
);
