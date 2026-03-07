/**
 * テーブル名変更フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import {
  extractApiErrorMessage,
  getResponseErrorMessage,
  replaceParamNames,
} from "../../../../lib/utils/apiError";
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
        const response = await getEconomiconAPI().renameTable({
          oldTableName: tableName,
          newTableName: value.newTableName,
        });
        if (response.code === "OK") {
          // テーブル一覧を再取得してストアを更新
          const listRes = await getEconomiconAPI().getTableList();
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
                newTableName: t("RenameTableForm.NewTableName"),
                oldTableName: t("RenameTableForm.CurrentTableName"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              newTableName: t("RenameTableForm.NewTableName"),
              oldTableName: t("RenameTableForm.CurrentTableName"),
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
              label={t("RenameTableForm.NewTableName")}
              htmlFor="rt-new-name"
              error={errorMsg}
            >
              <InputText
                id="rt-new-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("RenameTableForm.NewTableNamePlaceholder")}
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
