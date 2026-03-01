/**
 * 変換列追加フォーム（対数・べき乗・累乗根）
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

type TransformMethod = "log" | "power" | "root";

export const TransformColumnForm = ({
  tableName,
  column,
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const form = useForm({
    defaultValues: {
      method: "log" as TransformMethod,
      newColumnName: `log_${column.name}`,
      base: "",
      exponent: "2",
      degree: "2",
    },
    validators: {
      onSubmit: z.object({
        method: z.enum(["log", "power", "root"]),
        newColumnName: z
          .string()
          .min(1, t("ValidationMessages.NewColumnNameRequired")),
        base: z.string(),
        exponent: z.string(),
        degree: z.string(),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        let transformMethod;
        if (value.method === "log") {
          transformMethod = {
            method: "log" as const,
            logBase: value.base.trim() ? parseFloat(value.base) : null,
          };
        } else if (value.method === "power") {
          transformMethod = {
            method: "power" as const,
            exponent: parseFloat(value.exponent),
          };
        } else {
          transformMethod = {
            method: "root" as const,
            rootIndex: parseFloat(value.degree),
          };
        }

        const response = await getEconomiconAPI().transformColumn({
          tableName,
          sourceColumnName: column.name,
          newColumnName: value.newColumnName,
          addPositionColumn: column.name,
          transformMethod,
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
  const method = useStore(form.store, (s) => s.values.method);

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
        <form.Field name="method">
          {(field) => (
            <FormField
              label={t("TransformColumnForm.Method")}
              htmlFor="tf-method"
            >
              <Select
                id="tf-method"
                value={field.state.value}
                onValueChange={(v) => {
                  field.handleChange(v as TransformMethod);
                  // auto-update new column name prefix
                  form.setFieldValue(
                    "newColumnName",
                    v === "log"
                      ? `log_${column.name}`
                      : v === "power"
                        ? `pow_${column.name}`
                        : `root_${column.name}`,
                  );
                }}
                disabled={isSubmitting}
              >
                <SelectItem value="log">
                  {t("TransformColumnForm.MethodLog")}
                </SelectItem>
                <SelectItem value="power">
                  {t("TransformColumnForm.MethodPower")}
                </SelectItem>
                <SelectItem value="root">
                  {t("TransformColumnForm.MethodRoot")}
                </SelectItem>
              </Select>
            </FormField>
          )}
        </form.Field>

        {method === "log" && (
          <form.Field name="base">
            {(field) => (
              <FormField
                label={t("TransformColumnForm.Base")}
                htmlFor="tf-base"
              >
                <InputText
                  id="tf-base"
                  type="number"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder="e (自然対数)"
                  disabled={isSubmitting}
                />
              </FormField>
            )}
          </form.Field>
        )}

        {method === "power" && (
          <form.Field name="exponent">
            {(field) => (
              <FormField
                label={t("TransformColumnForm.Exponent")}
                htmlFor="tf-exponent"
              >
                <InputText
                  id="tf-exponent"
                  type="number"
                  step="0.1"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  disabled={isSubmitting}
                />
              </FormField>
            )}
          </form.Field>
        )}

        {method === "root" && (
          <form.Field name="degree">
            {(field) => (
              <FormField
                label={t("TransformColumnForm.Degree")}
                htmlFor="tf-degree"
              >
                <InputText
                  id="tf-degree"
                  type="number"
                  step="1"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  disabled={isSubmitting}
                />
              </FormField>
            )}
          </form.Field>
        )}
      </div>

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
              label={t("TransformColumnForm.NewColumnName")}
              htmlFor="tf-new-name"
              error={errorMsg}
            >
              <InputText
                id="tf-new-name"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("TransformColumnForm.NewColumnNamePlaceholder")}
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
          {isSubmitting ? "..." : t("TransformColumnForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
