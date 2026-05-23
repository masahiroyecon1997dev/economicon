/**
 * 列名変更フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { getEconomiconAppAPI } from "@/api/endpoints";
import { RenameColumnBody } from "@/api/zod/column/column";
import { useFormSubmitting } from "@/hooks/useFormSubmitting";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { InputText } from "@/components/atoms/Input/InputText";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { FormField } from "@/components/molecules/Form/FormField";
import { fetchUpdatedColumnList } from "@/components/organisms/Dialog/ColumnOperationForms/fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "@/components/organisms/Dialog/ColumnOperationForms/types";

export const RenameColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: { newColumnName: "" },
    validators: {
      onSubmit: RenameColumnBody.pick({ newColumnName: true }),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const response = await getEconomiconAppAPI().renameColumn({
          tableName,
          oldColumnName: column.name,
          newColumnName: value.newColumnName,
        });
        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          setApiError(
            buildResponseErrorMessage(response, t("Error.UnexpectedError"), {
              newColumnName: t("RenameColumnForm.NewColumnName"),
              oldColumnName: t("RenameColumnForm.CurrentColumnName"),
            }),
          );
        }
      } catch (error) {
        setApiError(
          buildCaughtErrorMessage(error, t("Error.UnexpectedError"), {
            newColumnName: t("RenameColumnForm.NewColumnName"),
            oldColumnName: t("RenameColumnForm.CurrentColumnName"),
          }),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);
  useFormSubmitting(isSubmitting, onIsSubmittingChange);

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
      <FormField label={t("RenameColumnForm.CurrentColumnName")}>
        <p className="rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-sm text-gray-600 font-mono">
          {column.name}
        </p>
      </FormField>

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
            ? extractFieldError(field.state.meta.errors)
            : undefined;
          return (
            <FormField
              label={t("RenameColumnForm.NewColumnName")}
              htmlFor="new-column-name"
              error={errorMsg}
            >
              <InputText
                id="new-column-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("RenameColumnForm.NewColumnNamePlaceholder")}
                disabled={isSubmitting}
                autoFocus
              />
            </FormField>
          );
        }}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
