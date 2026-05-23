import { getEconomiconAppAPI } from "@/api/endpoints";
import { AddPanelTimeColumnBody } from "@/api/zod/column/column";
import { InputText } from "@/components/atoms/Input/InputText";
import { Select, SelectItem } from "@/components/atoms/Input/Select";
import { ErrorAlert } from "@/components/molecules/Alert/ErrorAlert";
import { FormField } from "@/components/molecules/Form/FormField";
import { fetchUpdatedColumnList } from "@/components/organisms/Dialog/ColumnOperationForms/fetchUpdatedColumnList";
import type { ColumnOperationFormPropsType } from "@/components/organisms/Dialog/ColumnOperationForms/types";
import { useFormSubmitting } from "@/hooks/useFormSubmitting";
import {
  buildCaughtErrorMessage,
  buildResponseErrorMessage,
} from "@/lib/utils/apiError";
import { extractFieldError } from "@/lib/utils/formHelpers";
import { useTableInfosStore } from "@/stores/tableInfos";
import { useForm, useStore } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { z } from "zod";

const EMPTY_COLUMNS: { name: string; type: string }[] = [];

const buildDefaultColumnName = (columnName: string) => `time_${columnName}`;

const parseNumber = (value: string) => Number(value.trim());

const buildAddPanelTimeColumnFormSchema = (t: (key: string) => string) =>
  z.object({
    idColumn: AddPanelTimeColumnBody.shape.idColumn,
    newColumnName: AddPanelTimeColumnBody.shape.newColumnName,
    startValue: z
      .string()
      .trim()
      .min(1, t("AddPanelTimeColumnForm.StartValueError"))
      .refine(
        (value) => Number.isFinite(parseNumber(value)),
        t("AddPanelTimeColumnForm.StartValueError"),
      ),
    step: z
      .string()
      .trim()
      .min(1, t("AddPanelTimeColumnForm.StepNumberError"))
      .refine(
        (value) => Number.isFinite(parseNumber(value)),
        t("AddPanelTimeColumnForm.StepNumberError"),
      )
      .refine(
        (value) => parseNumber(value) !== 0,
        t("AddPanelTimeColumnForm.StepError"),
      ),
  });

export const AddPanelTimeColumnForm = ({
  tableName,
  column,
  formId,
  onIsSubmittingChange,
  onSuccess,
}: ColumnOperationFormPropsType) => {
  const { t } = useTranslation();
  const [apiError, setApiError] = useState<string | null>(null);

  const allColumns = useTableInfosStore(
    (state) =>
      state.tableInfos.find((info) => info.tableName === tableName)
        ?.columnList ?? EMPTY_COLUMNS,
  );

  const form = useForm({
    defaultValues: {
      idColumn: column.name,
      newColumnName: buildDefaultColumnName(column.name),
      startValue: "1",
      step: "1",
    },
    validators: {
      onSubmit: buildAddPanelTimeColumnFormSchema(t),
    },
    onSubmit: async ({ value }) => {
      setApiError(null);

      try {
        const payload = AddPanelTimeColumnBody.parse({
          tableName,
          idColumn: value.idColumn,
          newColumnName: value.newColumnName,
          addPositionColumn: column.name,
          startValue: parseNumber(value.startValue),
          step: parseNumber(value.step),
        });

        const response =
          await getEconomiconAppAPI().addPanelTimeColumn(payload);

        if (response.code === "OK") {
          const updatedList = await fetchUpdatedColumnList(tableName);
          onSuccess(updatedList);
        } else {
          setApiError(
            buildResponseErrorMessage(response, t("Error.UnexpectedError"), {
              idColumn: t("AddPanelTimeColumnForm.IdColumn"),
              newColumnName: t("AddPanelTimeColumnForm.NewColumnName"),
              addPositionColumn: t("AddPanelTimeColumnForm.AddPosition"),
              startValue: t("AddPanelTimeColumnForm.StartValue"),
              step: t("AddPanelTimeColumnForm.Step"),
            }),
          );
        }
      } catch (error) {
        setApiError(
          buildCaughtErrorMessage(error, t("Error.UnexpectedError"), {
            idColumn: t("AddPanelTimeColumnForm.IdColumn"),
            newColumnName: t("AddPanelTimeColumnForm.NewColumnName"),
            addPositionColumn: t("AddPanelTimeColumnForm.AddPosition"),
            startValue: t("AddPanelTimeColumnForm.StartValue"),
            step: t("AddPanelTimeColumnForm.Step"),
          }),
        );
      }
    },
  });

  const isSubmitting = useStore(form.store, (state) => state.isSubmitting);
  useFormSubmitting(isSubmitting, onIsSubmittingChange);

  const handleIdColumnChange = (nextIdColumn: string) => {
    const previousIdColumn = form.getFieldValue("idColumn");
    const currentNewColumnName = form.getFieldValue("newColumnName");
    const previousDefaultName = buildDefaultColumnName(previousIdColumn);

    form.setFieldValue("idColumn", nextIdColumn);

    if (currentNewColumnName === previousDefaultName) {
      form.setFieldValue("newColumnName", buildDefaultColumnName(nextIdColumn));
    }
  };

  return (
    <form
      id={formId}
      onSubmit={(event) => {
        event.preventDefault();
        event.stopPropagation();
        void form.handleSubmit();
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <form.Field name="idColumn">
          {(field) => {
            const idColumnError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;

            return (
              <FormField
                label={t("AddPanelTimeColumnForm.IdColumn")}
                htmlFor="panel-time-id-column"
                error={idColumnError}
              >
                <div data-testid="panel-time-id-column">
                  <Select
                    id="panel-time-id-column"
                    value={field.state.value}
                    onValueChange={(value) => {
                      handleIdColumnChange(value);
                      field.handleBlur();
                    }}
                    disabled={isSubmitting || allColumns.length === 0}
                    error={idColumnError}
                  >
                    {allColumns.map((currentColumn) => (
                      <SelectItem
                        key={currentColumn.name}
                        value={currentColumn.name}
                      >
                        {currentColumn.name}
                      </SelectItem>
                    ))}
                  </Select>
                </div>
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
            const newColumnNameError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;

            return (
              <FormField
                label={t("AddPanelTimeColumnForm.NewColumnName")}
                htmlFor="panel-time-new-column-name"
                error={newColumnNameError}
              >
                <InputText
                  id="panel-time-new-column-name"
                  data-testid="panel-time-new-column-name"
                  value={field.state.value}
                  onChange={(event) => field.handleChange(event.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t(
                    "AddPanelTimeColumnForm.NewColumnNamePlaceholder",
                  )}
                  disabled={isSubmitting}
                />
              </FormField>
            );
          }}
        </form.Field>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <form.Field
          name="startValue"
          validators={{
            onChange: ({ value }) => {
              if (value.trim().length === 0) {
                return t("AddPanelTimeColumnForm.StartValueError");
              }

              return Number.isFinite(parseNumber(value))
                ? undefined
                : t("AddPanelTimeColumnForm.StartValueError");
            },
          }}
        >
          {(field) => {
            const startValueError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;

            return (
              <FormField
                label={t("AddPanelTimeColumnForm.StartValue")}
                htmlFor="panel-time-start-value"
                error={startValueError}
              >
                <InputText
                  id="panel-time-start-value"
                  data-testid="panel-time-start-value"
                  type="number"
                  step="1"
                  value={field.state.value}
                  onChange={(event) => field.handleChange(event.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t(
                    "AddPanelTimeColumnForm.StartValuePlaceholder",
                  )}
                  disabled={isSubmitting}
                />
              </FormField>
            );
          }}
        </form.Field>

        <form.Field
          name="step"
          validators={{
            onChange: ({ value }) => {
              if (value.trim().length === 0) {
                return t("AddPanelTimeColumnForm.StepNumberError");
              }

              const parsedValue = parseNumber(value);

              if (!Number.isFinite(parsedValue)) {
                return t("AddPanelTimeColumnForm.StepNumberError");
              }

              return parsedValue === 0
                ? t("AddPanelTimeColumnForm.StepError")
                : undefined;
            },
          }}
        >
          {(field) => {
            const stepError = field.state.meta.isTouched
              ? extractFieldError(field.state.meta.errors)
              : undefined;

            return (
              <FormField
                label={t("AddPanelTimeColumnForm.Step")}
                htmlFor="panel-time-step"
                error={stepError}
              >
                <InputText
                  id="panel-time-step"
                  data-testid="panel-time-step"
                  type="number"
                  step="1"
                  value={field.state.value}
                  onChange={(event) => field.handleChange(event.target.value)}
                  onBlur={field.handleBlur}
                  placeholder={t("AddPanelTimeColumnForm.StepPlaceholder")}
                  disabled={isSubmitting}
                />
              </FormField>
            );
          }}
        </form.Field>
      </div>

      <div
        data-testid="panel-time-position"
        className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600"
      >
        {t("AddPanelTimeColumnForm.AddPositionDescription", {
          columnName: column.name,
        })}
      </div>

      {apiError && <ErrorAlert message={apiError} />}
    </form>
  );
};
