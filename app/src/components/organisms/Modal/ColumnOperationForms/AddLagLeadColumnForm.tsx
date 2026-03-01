/**
 * ラグ・リード列追加フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

export const AddLagLeadColumnForm = ({
  tableName,
  column,
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const form = useForm({
    defaultValues: {
      periods: "-1",
      newColumnName: `lag1_${column.name}`,
      groupColumnsRaw: "",
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
        groupColumnsRaw: z.string(),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        const groupColumns = value.groupColumnsRaw
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);

        const periods = parseInt(value.periods, 10);

        const response = await getEconomiconAPI().addLagLeadColumn({
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
              ? (field.state.meta.errors[0] as string | undefined)
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
              ? (field.state.meta.errors[0] as string | undefined)
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

      <form.Field name="groupColumnsRaw">
        {(field) => (
          <FormField
            label={t("AddLagLeadColumnForm.GroupColumns")}
            htmlFor="lag-group-cols"
          >
            <InputText
              id="lag-group-cols"
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              onBlur={field.handleBlur}
              placeholder="例: city, region（カンマ区切り）"
              disabled={isSubmitting}
            />
          </FormField>
        )}
      </form.Field>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("AddLagLeadColumnForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
