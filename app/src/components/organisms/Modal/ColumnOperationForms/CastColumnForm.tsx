/**
 * 列型変換フォーム
 */
import { useForm, useStore } from "@tanstack/react-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { getEconomiconAPI } from "../../../../api/endpoints";
import { showMessageDialog } from "../../../../lib/dialog/message";
import { Button } from "../../../atoms/Button/Button";
import { InputText } from "../../../atoms/Input/InputText";
import { Select, SelectItem } from "../../../atoms/Input/Select";
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
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

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
      onSubmit: z.object({
        targetType: z.enum(TARGET_TYPES),
        newColumnName: z
          .string()
          .min(1, t("ValidationMessages.NewColumnNameRequired")),
        cleanupWhitespace: z.boolean(),
        removeCommas: z.boolean(),
        datetimeFormat: z.string(),
        strict: z.boolean(),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        const response = await getEconomiconAPI().castColumn({
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
  const targetType = useStore(form.store, (s) => s.values.targetType);

  const isStringSource =
    column.type.includes("Utf8") || column.type.includes("String");
  const isDateTarget = targetType === "date" || targetType === "datetime";

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
        <form.Field name="targetType">
          {(field) => (
            <FormField
              label={t("CastColumnForm.TargetType")}
              htmlFor="cast-target-type"
              error={field.state.meta.errors[0]?.toString()}
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
              ? (field.state.meta.errors[0] as string | undefined)
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

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("CastColumnForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
