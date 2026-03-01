/**
 * ダミー変数追加フォーム
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

type DummyMode = "single" | "all_except_base";
type NullStrategy = "exclude" | "as_category" | "error";

export const AddDummyColumnForm = ({
  tableName,
  column,
  onSuccess,
  onClose,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const form = useForm({
    defaultValues: {
      mode: "single" as DummyMode,
      targetValue: "",
      dummyColumnName: `is_${column.name}`,
      dropBaseValue: "auto_most_frequent",
      nullStrategy: "exclude" as NullStrategy,
    },
    validators: {
      onSubmit: z.object({
        mode: z.enum(["single", "all_except_base"]),
        targetValue: z.string(),
        dummyColumnName: z.string(),
        dropBaseValue: z.string(),
        nullStrategy: z.enum(["exclude", "as_category", "error"]),
      }),
    },
    onSubmit: async ({ value }) => {
      try {
        const response = await getEconomiconAPI().addDummyColumn({
          tableName,
          sourceColumnName: column.name,
          addPositionColumn: column.name,
          mode: value.mode,
          targetValue: value.mode === "single" ? value.targetValue : null,
          dummyColumnName:
            value.mode === "single" ? value.dummyColumnName : null,
          dropBaseValue:
            value.mode === "all_except_base" ? value.dropBaseValue : null,
          nullStrategy: value.nullStrategy,
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
  const mode = useStore(form.store, (s) => s.values.mode);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        e.stopPropagation();
        void form.handleSubmit();
      }}
      className="space-y-4"
    >
      <form.Field name="mode">
        {(field) => (
          <FormField label={t("AddDummyColumnForm.Mode")} htmlFor="dummy-mode">
            <Select
              id="dummy-mode"
              value={field.state.value}
              onValueChange={(v) => field.handleChange(v as DummyMode)}
              disabled={isSubmitting}
            >
              <SelectItem value="single">
                {t("AddDummyColumnForm.ModeSingle")}
              </SelectItem>
              <SelectItem value="all_except_base">
                {t("AddDummyColumnForm.ModeAllExceptBase")}
              </SelectItem>
            </Select>
          </FormField>
        )}
      </form.Field>

      {mode === "single" && (
        <>
          <form.Field name="targetValue">
            {(field) => (
              <FormField
                label={t("AddDummyColumnForm.TargetValue")}
                htmlFor="dummy-target-value"
                error={field.state.meta.errors[0]?.toString()}
              >
                <InputText
                  id="dummy-target-value"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t("AddDummyColumnForm.TargetValuePlaceholder")}
                  error={field.state.meta.errors[0]?.toString()}
                  disabled={isSubmitting}
                  autoFocus
                />
              </FormField>
            )}
          </form.Field>

          <form.Field name="dummyColumnName">
            {(field) => (
              <FormField
                label={t("AddDummyColumnForm.DummyColumnName")}
                htmlFor="dummy-col-name"
                error={field.state.meta.errors[0]?.toString()}
              >
                <InputText
                  id="dummy-col-name"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t(
                    "AddDummyColumnForm.DummyColumnNamePlaceholder",
                  )}
                  error={field.state.meta.errors[0]?.toString()}
                  disabled={isSubmitting}
                />
              </FormField>
            )}
          </form.Field>
        </>
      )}

      {mode === "all_except_base" && (
        <form.Field name="dropBaseValue">
          {(field) => (
            <FormField
              label={t("AddDummyColumnForm.DropBaseValue")}
              htmlFor="dummy-drop-base"
            >
              <InputText
                id="dummy-drop-base"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                placeholder={t("AddDummyColumnForm.DropBaseValuePlaceholder")}
                disabled={isSubmitting}
                autoFocus
              />
            </FormField>
          )}
        </form.Field>
      )}

      <form.Field name="nullStrategy">
        {(field) => (
          <FormField
            label={t("AddDummyColumnForm.NullStrategy")}
            htmlFor="dummy-null-strategy"
          >
            <Select
              id="dummy-null-strategy"
              value={field.state.value}
              onValueChange={(v) => field.handleChange(v as NullStrategy)}
              disabled={isSubmitting}
            >
              <SelectItem value="exclude">
                {t("AddDummyColumnForm.NullStrategyExclude")}
              </SelectItem>
              <SelectItem value="as_category">
                {t("AddDummyColumnForm.NullStrategyAsCategory")}
              </SelectItem>
              <SelectItem value="error">
                {t("AddDummyColumnForm.NullStrategyError")}
              </SelectItem>
            </Select>
          </FormField>
        )}
      </form.Field>

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
          {t("Common.Cancel")}
        </Button>
        <Button variant="primary" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "..." : t("AddDummyColumnForm.Submit")}
        </Button>
      </div>
    </form>
  );
};
