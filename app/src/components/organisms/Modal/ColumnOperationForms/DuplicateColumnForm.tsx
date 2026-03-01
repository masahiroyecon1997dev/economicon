/**
 * 列複製フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

export const DuplicateColumnForm = ({
  tableName,
  column,
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const form = useForm({
    defaultValues: { newColumnName: `${column.name}_copy` },
    validators: {
      onSubmit: z.object({
        newColumnName: z
          .string()
          .min(1, t("ValidationMessages.NewColumnNameRequired")),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        const response = await getEconomiconAPI().duplicateColumn({
          tableName,
          sourceColumnName: column.name,
          newColumnName: value.newColumnName,
          addPositionColumn: column.name,
        });
        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          await showMessageDialog(
            t("Error.Error"),
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                newColumnName: t("DuplicateColumnForm.NewColumnName"),
                sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
              },
            ),
          );
        }
      } catch (error) {
        await showMessageDialog(
          t("Error.Error"),
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              newColumnName: t("DuplicateColumnForm.NewColumnName"),
              sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
            },
          ),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (s) => s.isSubmitting);

  return (
    <form
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
              label={t("DuplicateColumnForm.NewColumnName")}
              htmlFor="dup-new-column-name"
              error={errorMsg}
            >
              <InputText
                id="dup-new-column-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("DuplicateColumnForm.NewColumnNamePlaceholder")}
                disabled={isSubmitting}
                autoFocus
              />
            </FormField>
          );
        }}
      </form.Field>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("DuplicateColumnForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
