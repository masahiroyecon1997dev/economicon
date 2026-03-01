/**
 * テーブル名変更フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import { useTableInfosStore } from "../../../../stores/tableInfos";
import { useTableListStore } from "../../../../stores/tableList";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { FormField } from "../../../molecules/Form/FormField";

type RenameTableFormProps = {
  tableName: string;
  onSuccess: () => void;
  onClose: () => void;
};

export const RenameTableForm = ({
  tableName,
  onSuccess,
  onClose,
}: RenameTableFormProps) => {
  const { t } = useTranslation();
  const setTableList = useTableListStore((s) => s.setTableList);
  const updateTableInfo = useTableInfosStore((s) => s.updateTableInfo);
  const tableInfos = useTableInfosStore((s) => s.tableInfos);

  const hasControlChars = (s: string) =>
    s.split("").some((c) => c.charCodeAt(0) < 32 || c.charCodeAt(0) === 127);

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
          }
          onSuccess();
        } else {
          await showMessageDialog(t("Error.Error"), t("Error.UnexpectedError"));
        }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : t("Error.UnexpectedError");
        await showMessageDialog(t("Error.Error"), message);
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

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("RenameTableForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
