/**
 * 列名変更フォーム
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
import { InputText } from "../../../atoms/Input/InputText";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

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
      onSubmit: z.object({
        newColumnName: z
          .string()
          .min(1, t("ValidationMessages.NewColumnNameRequired")),
      }),
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
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                newColumnName: t("RenameColumnForm.NewColumnName"),
                oldColumnName: t("RenameColumnForm.CurrentColumnName"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              newColumnName: t("RenameColumnForm.NewColumnName"),
              oldColumnName: t("RenameColumnForm.CurrentColumnName"),
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
            ? (field.state.meta.errors[0] as string | undefined)
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
