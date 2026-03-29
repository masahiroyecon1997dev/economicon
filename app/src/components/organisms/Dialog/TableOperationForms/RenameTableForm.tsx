/**
 * テーブル名変更フォーム
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
import { useTableListStore } from "../../../../stores/tableList";
import { InputText } from "../../../atoms/Input/InputText";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";

type RenameTableFormProps = {
  tableName: string;
  onSuccess: () => void;
  formId: string;
  onIsSubmittingChange: (isSubmitting: boolean) => void;
};

export const RenameTableForm = ({
  tableName,
  onSuccess,
  formId,
  onIsSubmittingChange,
}: RenameTableFormProps) => {
  const { t } = useTranslation();
  const setTableList = useTableListStore((s) => s.setTableList);
  const updateTableInfo = useTableInfosStore((s) => s.updateTableInfo);
  const tableInfos = useTableInfosStore((s) => s.tableInfos);
  const activeTableName = useTableInfosStore((s) => s.activeTableName);

  const hasControlChars = (s: string) =>
    s.split("").some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127);

  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: { newTableName: tableName },
    validators: {
      onSubmit: z.object({
        newTableName: z
          .string()
          .min(1, t("ValidationMessages.DataNameRequired"))
          .max(128, t("ValidationMessages.DataNameTooLong"))
          .refine(
            (v) => !hasControlChars(v),
            t("ValidationMessages.DataNameInvalidChars"),
          ),
      }),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);
      try {
        const response = await getEconomiconAppAPI().renameTable({
          oldTableName: tableName,
          newTableName: value.newTableName,
        });
        if (response.code === "OK") {
          // テーブル一覧を再取得してストアを更新
          const listRes = await getEconomiconAppAPI().getTableList();
          if (listRes.code === "OK") {
            setTableList(listRes.result.tableNameList);
          }
          // tableInfos の該当エントリのテーブル名を更新
          const info = tableInfos.find((i) => i.tableName === tableName);
          if (info) {
            updateTableInfo(tableName, {
              ...info,
              tableName: value.newTableName,
            });
            // activeTableName は tableInfos とは別フィールドなので別途更新
            if (activeTableName === tableName) {
              useTableInfosStore.setState({
                activeTableName: value.newTableName,
              });
            }
          }
          onSuccess();
        } else {
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                newTableName: t("RenameTableForm.NewDataName"),
                oldTableName: t("RenameTableForm.CurrentDataName"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              newTableName: t("RenameTableForm.NewDataName"),
              oldTableName: t("RenameTableForm.CurrentDataName"),
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
      <form.Field
        name="newTableName"
        validators={{
          onChange: ({ value }) => {
            if (!value.trim()) return t("ValidationMessages.DataNameRequired");
            if (value.length > 128)
              return t("ValidationMessages.DataNameTooLong");
            if (hasControlChars(value))
              return t("ValidationMessages.DataNameInvalidChars");
            return undefined;
          },
        }}
      >
        {(field) => {
          const errorMsg = field.state.meta.isTouched
            ? extractFieldError(field.state.meta.errors)
            : undefined;
          return (
            <FormField
              label={t("RenameTableForm.NewDataName")}
              htmlFor="rt-new-name"
              error={errorMsg}
            >
              <InputText
                id="rt-new-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("RenameTableForm.NewDataNamePlaceholder")}
                disabled={isSubmitting}
              />
            </FormField>
          );
        }}
      </form.Field>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
