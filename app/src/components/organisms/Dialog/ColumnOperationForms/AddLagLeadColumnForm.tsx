/**
 * ラグ・リード列追加フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
import { extractFieldError } from "../../../../lib/utils/formHelpers";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { InputText } from "../../../atoms/Input/InputText";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

const EMPTY_COLUMNS: { name: string; type: string }[] = [];

export const AddLagLeadColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const [apiError, setApiError] = useState<string | null>(null);

  const allColumns = useTableInfosStore(
    (s) =>
      s.tableInfos.find((i) => i.tableName === tableName)?.columnList ??
      EMPTY_COLUMNS,
  );

  const form = useForm({
    defaultValues: {
      periods: "-1",
      newColumnName: `lag1_${column.name}`,
      groupColumns: [] as string[],
    },
    validators: {
      onSubmit: z.object({
        periods: z
          .string()
          .refine(
            (v) => !isNaN(parseInt(v, 10)) && parseInt(v, 10) !== 0,
            "0 以外の整数で入力してください。",
          ),
        newColumnName: z
          .string()
          .min(1, t("ValidationMessages.NewColumnNameRequired")),
        groupColumns: z.array(z.string()),
      }),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const groupColumns = value.groupColumns;

        const periods = parseInt(value.periods, 10);

        const response = await getEconomiconAppAPI().addLagLeadColumn({
          tableName,
          sourceColumn: column.name,
          newColumnName: value.newColumnName,
          addPositionColumn: column.name,
          periods,
          groupColumns,
        });
        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                newColumnName: t("AddLagLeadColumnForm.NewColumnName"),
                sourceColumn: t("ColumnOperationForm.SourceColumnName"),
                periods: t("AddLagLeadColumnForm.Periods"),
                groupColumns: t("AddLagLeadColumnForm.GroupColumns"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              newColumnName: t("AddLagLeadColumnForm.NewColumnName"),
              sourceColumn: t("ColumnOperationForm.SourceColumnName"),
              periods: t("AddLagLeadColumnForm.Periods"),
              groupColumns: t("AddLagLeadColumnForm.GroupColumns"),
            },
          ),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  useEffect(() => {
    onIsSubmittingChange(isSubmitting);
  }, [isSubmitting, onIsSubmittingChange]);
  const periods = useStore(form.store, (s) => s.values.periods);

  const handlePeriodsChange = (value: string) => {
    form.setFieldValue("periods", value);
    const n = parseInt(value, 10);
    if (!isNaN(n) && n !== 0) {
      const prefix = n < 0 ? `lag${Math.abs(n)}` : `lead${n}`;
      form.setFieldValue("newColumnName", `${prefix}_${column.name}`);
    }
  };

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
      <div className="grid grid-cols-2 gap-4">
        <form.Field
          name="periods"
          validators={{
            onChange: ({ value }) => {
              const n = parseInt(value, 10);
              return isNaN(n) || n === 0
                ? t("AddLagLeadColumnForm.PeriodsError")
                : undefined;
            },
          }}
        >
          {(field) => {
            const periodsError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;
            return (
              <FormField
                label={t("AddLagLeadColumnForm.Periods")}
                htmlFor="lag-periods"
                error={periodsError}
              >
                <InputText
                  id="lag-periods"
                  type="number"
                  value={field.state.value}
                  onChange={(e) => {
                    field.handleChange(e.target.value);
                    handlePeriodsChange(e.target.value);
                  }}
                  onBlur={field.handleBlur}
                  placeholder={t("AddLagLeadColumnForm.PeriodsPlaceholder")}
                  disabled={isSubmitting}
                  autoFocus
                />
              </FormField>
            );
          }}
        </form.Field>

        <form.Field
          name="newColumnName"
          validators={{
            onChange: ({ value }) =>
              value.trim().length === 0
                ? t("ValidationMessages.NewColumnNameRequired")
                : undefined,
          }}
        >
          {(field) => {
            const nameError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;
            return (
              <FormField
                label={t("AddLagLeadColumnForm.NewColumnName")}
                htmlFor="lag-new-name"
                error={nameError}
              >
                <InputText
                  id="lag-new-name"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t(
                    "AddLagLeadColumnForm.NewColumnNamePlaceholder",
                  )}
                  disabled={isSubmitting}
                />
              </FormField>
            );
          }}
        </form.Field>
      </div>

      {/* 期間の符号による説明 */}
      {periods && parseInt(periods, 10) !== 0 && (
        <p className="text-xs text-gray-500">
          {parseInt(periods, 10) < 0
            ? `ラグ ${Math.abs(parseInt(periods, 10))} 期前の値を追加します。`
            : `リード ${parseInt(periods, 10)} 期後の値を追加します。`}
        </p>
      )}

      <form.Field name="groupColumns">
        {(field) => (
          <FormField
            label={t("AddLagLeadColumnForm.GroupColumns")}
            htmlFor="lag-group-cols"
          >
            <div className="space-y-1 max-h-36 overflow-y-auto rounded-md border border-input bg-background p-2">
              {allColumns.length === 0 ? (
                <p className="text-xs text-gray-400">
                  {t("AddLagLeadColumnForm.NoColumns")}
                </p>
              ) : (
                allColumns.map((col) => (
                  <label
                    key={col.name}
                    className="flex items-center gap-2 text-sm cursor-pointer select-none"
                  >
                    <input
                      type="checkbox"
                      checked={field.state.value.includes(col.name)}
                      onChange={(e) => {
                        const next = e.target.checked
                          ? [...field.state.value, col.name]
                          : field.state.value.filter((n) => n !== col.name);
                        field.handleChange(next);
                      }}
                      disabled={isSubmitting}
                      className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                    />
                    {col.name}
                  </label>
                ))
              )}
            </div>
          </FormField>
        )}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
