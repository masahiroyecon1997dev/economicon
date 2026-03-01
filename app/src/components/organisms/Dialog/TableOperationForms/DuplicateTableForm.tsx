/**
 * テーブル複製フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
import { useTableListStore } from "../../../../stores/tableList";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";

type DuplicateTableFormProps = {
  tableName: string;
  onSuccess: () => void;
  onClose: () => void;
};

export const DuplicateTableForm = ({
  tableName,
  onSuccess,
  onClose,
}: DuplicateTableFormProps) => {
  const { t } = useTranslation();
  const setTableList = useTableListStore((s) => s.setTableList);

  const hasControlChars = (s: string) =>
    s.split("").some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127);

  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: { newTableName: `${tableName}_copy` },
    validators: {
      onSubmit: z.object({
        newTableName: z
          .string()
          .min(1, t("ValidationMessages.TableNameRequired"))
          .max(128, t("ValidationMessages.TableNameTooLong"))
          .refine(
            (v) => !hasControlChars(v),
            t("ValidationMessages.TableNameInvalidChars"),
          ),
      }),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const response = await getEconomiconAPI().duplicateTable({
          tableName,
          newTableName: value.newTableName,
        });
        if (response.code === "OK") {
          const listRes = await getEconomiconAPI().getTableList();
          if (listRes.code === "OK") {
            setTableList(listRes.result.tableNameList);
          }
          onSuccess();
        } else {
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              { newTableName: t("DuplicateTableForm.NewTableName") },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            { newTableName: t("DuplicateTableForm.NewTableName") },
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
      <form.Field
        name="newTableName"
        validators={{
          onChange: ({ value }) => {
            if (!value.trim()) return t("ValidationMessages.TableNameRequired");
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
              label={t("DuplicateTableForm.NewTableName")}
              htmlFor="dt-new-name"
              error={errorMsg}
            >
              <InputText
                id="dt-new-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("DuplicateTableForm.NewTableNamePlaceholder")}
                disabled={isSubmitting}
              />
            </FormField>
          );
        }}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("DuplicateTableForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
