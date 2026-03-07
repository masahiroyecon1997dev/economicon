/**
 * ダミー変数追加フォーム
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
import { InputText } from "../../../atoms/Input/InputText";
import { Select, SelectItem } from "../../../atoms/Input/Select";
import { ErrorAlert } from "../../../molecules/Alert/ErrorAlert";
import { FormField } from "../../../molecules/Form/FormField";
import { fetchUpdatedColumnList } from "./fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "./types";

type DummyMode = "single" | "all_except_base";
type NullStrategy = "exclude" | "as_category" | "error";

export const AddDummyColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();

  const [apiError, setApiError] = useState<string | null>(null);

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
      setApiError(null);
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
          setApiError(
            replaceParamNames(
              getResponseErrorMessage(response, t("Error.UnexpectedError")),
              {
                dummyColumnName: t("AddDummyColumnForm.DummyColumnName"),
                sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
                targetValue: t("AddDummyColumnForm.TargetValue"),
                nullStrategy: t("AddDummyColumnForm.NullStrategy"),
                dropBaseValue: t("AddDummyColumnForm.DropBaseValue"),
              },
            ),
          );
        }
      } catch (error) {
        setApiError(
          replaceParamNames(
            extractApiErrorMessage(error, t("Error.UnexpectedError")),
            {
              dummyColumnName: t("AddDummyColumnForm.DummyColumnName"),
              sourceColumnName: t("ColumnOperationForm.SourceColumnName"),
              targetValue: t("AddDummyColumnForm.TargetValue"),
              nullStrategy: t("AddDummyColumnForm.NullStrategy"),
              dropBaseValue: t("AddDummyColumnForm.DropBaseValue"),
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
  const mode = useStore(form.store, (s) => s.values.mode);

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
              >
                <InputText
                  id="dummy-target-value"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t("AddDummyColumnForm.TargetValuePlaceholder")}
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
              >
                <InputText
                  id="dummy-col-name"
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t(
                    "AddDummyColumnForm.DummyColumnNamePlaceholder",
                  )}
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

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
