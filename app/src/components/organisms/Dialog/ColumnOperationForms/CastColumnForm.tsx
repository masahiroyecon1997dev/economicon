/**
 * 列型変換フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAppAPI } from "../../../../api/endpoints";
import { CastColumnBody } from "../../../../api/zod/column/column";
import { useFormSubmitting } from "../../../../hooks/useFormSubmitting";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "../../../../lib/utils/apiError";
import {
  createFieldError,
  extractFieldError,
} from "../../../../lib/utils/formHelpers";
import { InputText } from "../../../atoms/Input/InputText";
import { Select, SelectItem } from "../../../atoms/Input/Select";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

const TARGET_TYPES = [
  "float",
  "int",
  "str",
  "bool",
  "date",
  "datetime",
] as const;

export const CastColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const tErr = createFieldError(t);

  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: {
      targetType: "float" as (typeof TARGET_TYPES)[number],
      newColumnName: `${column.name}_cast`,
      cleanupWhitespace: true,
      removeCommas: true,
      datetimeFormat: "",
      strict: false,
    },
    validators: {
      onSubmit: CastColumnBody.pick({
        targetType: true,
        newColumnName: true,
        cleanupWhitespace: true,
        removeCommas: true,
        strict: true,
      })
        .required()
        .extend(z.object({ datetimeFormat: z.string() }).shape),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const response = await getEconomiconAppAPI().castColumn({
          tableName,
          sourceColumnName: column.name,
          targetType: value.targetType,
          newColumnName: value.newColumnName,
          addPositionColumn: column.name,
          cleanupWhitespace: value.cleanupWhitespace,
          removeCommas: value.removeCommas,
          datetimeFormat: value.datetimeFormat.trim() || null,
          strict: value.strict,
        });
        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          setApiError(
            buildResponseErrorMessage(response, t("Error.UnexpectedError"), {
              newColumnName: t("CastColumnForm.NewColumnName"),
              sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
              targetType: t("CastColumnForm.TargetType"),
            }),
          );
        }
      } catch (error) {
        setApiError(
          buildCaughtErrorMessage(error, t("Error.UnexpectedError"), {
            newColumnName: t("CastColumnForm.NewColumnName"),
            sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
            targetType: t("CastColumnForm.TargetType"),
          }),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  useFormSubmitting(isSubmitting, onIsSubmittingChange);
  const targetType = useStore(form.store, (s) => s.values.targetType);

  const isStringSource =
    column.type.includes("Utf8") || column.type.includes("String");
  const isDateTarget = targetType === "date" || targetType === "datetime";

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
        <form.Field name="targetType">
          {(field) => (
            <FormField
              label={t("CastColumnForm.TargetType")}
              htmlFor="cast-target-type"
              error={extractFieldError(field.state.meta.errors)}
            >
              <Select
                id="cast-target-type"
                value={field.state.value}
                onValueChange={(v) =>
                  field.handleChange(v as (typeof TARGET_TYPES)[number])
                }
                disabled={isSubmitting}
              >
                {TARGET_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </Select>
            </FormField>
          )}
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
            const errorMsg = field.state.meta.isTouched
              ? tErr(
                  field.state.meta.errors,
                  "ValidationMessages.NewColumnNameRequired",
                )
              : undefined;
            return (
              <FormField
                label={t("CastColumnForm.NewColumnName")}
                htmlFor="cast-new-column-name"
                error={errorMsg}
              >
                <InputText
                  id="cast-new-column-name"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t("CastColumnForm.NewColumnNamePlaceholder")}
                  disabled={isSubmitting}
                />
              </FormField>
            );
          }}
        </form.Field>
      </div>

      {isStringSource && (
        <div className="space-y-2">
          <form.Field name="cleanupWhitespace">
            {(field) => (
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={field.state.value}
                  onChange={(e) => field.handleChange(e.target.checked)}
                  disabled={isSubmitting}
                  className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                />
                {t("CastColumnForm.CleanupWhitespace")}
              </label>
            )}
          </form.Field>

          <form.Field name="removeCommas">
            {(field) => (
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={field.state.value}
                  onChange={(e) => field.handleChange(e.target.checked)}
                  disabled={isSubmitting}
                  className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
                />
                {t("CastColumnForm.RemoveCommas")}
              </label>
            )}
          </form.Field>
        </div>
      )}

      {isDateTarget && (
        <form.Field name="datetimeFormat">
          {(field) => (
            <FormField
              label={t("CastColumnForm.DatetimeFormat")}
              htmlFor="cast-datetime-format"
            >
              <InputText
                id="cast-datetime-format"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("CastColumnForm.DatetimeFormatPlaceholder")}
                disabled={isSubmitting}
              />
            </FormField>
          )}
        </form.Field>
      )}

      <form.Field name="strict">
        {(field) => (
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={field.state.value}
              onChange={(e) => field.handleChange(e.target.checked)}
              disabled={isSubmitting}
              className="rounded border-gray-300 text-brand-primary focus:ring-brand-primary"
            />
            {t("CastColumnForm.Strict")}
          </label>
        )}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
